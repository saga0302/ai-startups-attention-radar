"""Load the versioned company seed file."""

from __future__ import annotations

import csv
from pathlib import Path


def load_seed(path: str | Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def title_to_entity(rows: list[dict[str, str]]) -> dict[str, str]:
    """Map normalized en.wikipedia titles to entity_id for every panel row.

    Rows with a blank title are skipped. Duplicate titles raise, because one
    article cannot belong to two entities.
    """
    mapping: dict[str, str] = {}
    for row in rows:
        title = row["en_wikipedia_title"].strip()
        if not title:
            continue
        if title in mapping:
            raise ValueError(f"duplicate title {title!r} for {row['entity_id']} and {mapping[title]}")
        mapping[title] = row["entity_id"]
    return mapping
