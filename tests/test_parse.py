from pageviews_anomaly.parse import (
    dump_url,
    filter_lines,
    normalize_title,
    parse_line,
)

MAPPING = {"Anthropic": "anthropic", "Hugging_Face": "hugging_face"}


def test_parse_line_basic():
    assert parse_line("en Anthropic 42 1000") == ("en", "Anthropic", 42)


def test_parse_line_three_fields_ok():
    assert parse_line("en Anthropic 42") == ("en", "Anthropic", 42)


def test_parse_line_malformed_returns_none():
    assert parse_line("en Anthropic") is None
    assert parse_line("en Anthropic abc 0") is None
    assert parse_line("en Anthropic -3 0") is None


def test_normalize_title_decodes_and_underscores():
    assert normalize_title("Hugging%20Face") == "Hugging_Face"
    assert normalize_title("Hugging Face") == "Hugging_Face"


def test_filter_keeps_only_in_scope_english_wikipedia():
    lines = [
        "en Anthropic 10 0",
        "de Anthropic 99 0",
        "en Main_Page 500 0",
        "en Hugging%20Face 7 0",
        "garbage line",
    ]
    records = list(filter_lines(lines, MAPPING, "2026-11-02T14:00:00Z"))
    assert [(r.entity_id, r.views) for r in records] == [("anthropic", 10), ("hugging_face", 7)]
    assert all(r.hour_utc == "2026-11-02T14:00:00Z" for r in records)


def test_dump_url_format():
    assert dump_url("2026-11-02T14:00:00Z") == (
        "https://dumps.wikimedia.org/other/pageviews/2026/2026-11/pageviews-20261102-140000.gz"
    )
