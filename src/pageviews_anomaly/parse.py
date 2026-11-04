"""Parse Wikimedia hourly pageview dump lines and filter them to in-scope articles.

Hourly dump lines (pageviews-YYYYMMDD-HHMMSS.gz, space-separated):

    domain_code page_title count_views [total_response_size]

Only the first three fields are required; the fourth is ignored.
"""

from __future__ import annotations

import urllib.parse
from dataclasses import dataclass
from typing import Iterable, Iterator, Mapping

from datetime import datetime, timezone


@dataclass(frozen=True)
class PageviewRecord:
    entity_id: str
    en_wikipedia_title: str
    hour_utc: str  # ISO-8601 hour, e.g. "2026-11-02T14:00:00Z"
    views: int


def normalize_title(raw_title: str) -> str:
    """Normalize a dump title for comparison: percent-decode, underscores for spaces."""
    return urllib.parse.unquote(raw_title).replace(" ", "_")


def parse_line(line: str) -> tuple[str, str, int] | None:
    """Return (domain_code, normalized_title, views) or None for malformed lines."""
    parts = line.rstrip("\n").split(" ")
    if len(parts) < 3:
        return None
    domain, title, views_raw = parts[0], parts[1], parts[2]
    try:
        views = int(views_raw)
    except ValueError:
        return None
    if views < 0:
        return None
    return domain, normalize_title(title), views

# Desktop and mobile web are both English Wikipedia. Their views are summed per article.
ENGLISH_WIKIPEDIA_DOMAINS = ("en", "en.m")

def filter_lines(
    lines: Iterable[str],
    title_to_entity: Mapping[str, str],
    hour_utc: str,
    domains: tuple[str, ...] = ENGLISH_WIKIPEDIA_DOMAINS,
) -> Iterator[PageviewRecord]:
    """Yield records for in-scope titles from one hour of dump lines.

    Desktop and mobile web rows are yielded separately; the caller sums them.
    """
    for line in lines:
        parsed = parse_line(line)
        if parsed is None:
            continue
        line_domain, title, views = parsed
        if line_domain not in domains:
            continue
        entity_id = title_to_entity.get(title)
        if entity_id is None:
            continue
        yield PageviewRecord(entity_id, title, hour_utc, views)


def dump_url(hour_utc_iso: str, base: str = "https://dumps.wikimedia.org/other/pageviews") -> str:
    """Build the hourly dump URL for an ISO hour such as '2026-11-02T14:00:00Z'."""

    dt = datetime.strptime(hour_utc_iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return (
        f"{base}/{dt:%Y}/{dt:%Y-%m}/"
        f"pageviews-{dt:%Y%m%d}-{dt:%H}0000.gz"
    )
