"""Download one hour of Wikimedia pageviews, filter it to the panel, and stage it.

Output is one gzipped CSV per hour, written atomically so a failed run never
leaves a partial file that looks complete.
"""

from __future__ import annotations

import csv
import gzip
import io
import logging
import os
import tempfile
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator

from pageviews_anomaly.parse import dump_url, filter_lines

USER_AGENT = "pageviews-anomaly-pipeline/0.1 (research; contact: project owner)"
OUTPUT_FIELDS = ["entity_id", "en_wikipedia_title", "hour_utc", "views"]

log = logging.getLogger(__name__)


def hour_is_published(hour_utc: str, timeout: int = 30) -> bool:
    """True when Wikimedia has this hour's dump file.

    404 means not published yet. A 429, 5xx, or network error is logged and
    treated as "not yet" so the sensor polls again; the sensor's timeout bounds
    the wait. Other errors raise, because they point to a real problem.
    """
    request = urllib.request.Request(dump_url(hour_utc), method="HEAD", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout):
            log.info("%s is published", hour_utc)
            return True
    except urllib.error.HTTPError as err:
        if err.code == 404:
            log.info("%s not published yet (HTTP 404)", hour_utc)
            return False
        if err.code == 429 or err.code >= 500:
            log.warning("%s check got HTTP %s, will retry", hour_utc, err.code)
            return False
        raise
    except OSError as err:
        # Covers URLError (no connection, DNS) and TimeoutError (server stopped responding).
        log.warning("%s check failed: %r, will retry", hour_utc, err)
        return False


def iter_dump_lines(url: str, timeout: int = 120) -> Iterator[str]:
    """Stream a gzipped dump over HTTP, yielding decoded lines without loading it all into memory."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        with gzip.GzipFile(fileobj=response) as gz:
            text = io.TextIOWrapper(gz, encoding="utf-8", errors="replace")
            yield from text


def stage_hour(
    hour_utc: str,
    seed_map: dict[str, str],
    out_dir: str | Path,
    lines: Iterable[str] | None = None,
) -> Path:
    """Filter one hour of dump lines to the panel and write them to out_dir.

    lines defaults to the live dump for hour_utc. Tests pass lines directly.
    Returns the path of the written file.
    """
    if lines is None:
        lines = iter_dump_lines(dump_url(hour_utc))

        # Sum desktop and mobile web views per article for this hour.
    totals: dict[tuple[str, str], int] = {}
    for r in filter_lines(lines, seed_map, hour_utc):
        key = (r.entity_id, r.en_wikipedia_title)
        totals[key] = totals.get(key, 0) + r.views

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    dt = datetime.strptime(hour_utc, "%Y-%m-%dT%H:%M:%SZ")
    final_path = out_dir / f"pageviews_{dt:%Y%m%d}-{dt:%H}0000.csv.gz"

    fd, tmp_name = tempfile.mkstemp(dir=out_dir, suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb") as gz:
                text = io.TextIOWrapper(gz, encoding="utf-8", newline="")
                writer = csv.writer(text)
                writer.writerow(OUTPUT_FIELDS)
                for (entity_id, title), views in sorted(totals.items()):
                    writer.writerow([entity_id, title, hour_utc, views])
                text.flush()
        os.replace(tmp_name, final_path)
    except BaseException:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)
        raise
    return final_path
