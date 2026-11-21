import csv
import gzip
from pathlib import Path

import pytest
from pageviews_anomaly import ingest
from pageviews_anomaly.ingest import OUTPUT_FIELDS, stage_hour
from pageviews_anomaly.seed import load_seed, title_to_entity

SEED = Path(__file__).resolve().parents[1] / "seeds" / "ai_companies.csv"


def test_real_seed_loads_and_titles_are_unique():
    rows = load_seed(SEED)
    assert len(rows) >= 40
    mapping = title_to_entity(rows)  # raises on duplicates
    assert "Anthropic" in mapping and mapping["Anthropic"] == "anthropic"


def test_every_row_has_role_and_known_status():
    rows = load_seed(SEED)
    assert {r["role"] for r in rows} <= {"startup", "reference"}
    assert all(r["title_status"] for r in rows)


def test_duplicate_title_raises():
    rows = [
        {"entity_id": "a", "en_wikipedia_title": "Same"},
        {"entity_id": "b", "en_wikipedia_title": "Same"},
    ]
    with pytest.raises(ValueError):
        title_to_entity(rows)


def test_blank_seed_title_is_skipped():
    rows = [{"entity_id": "a", "en_wikipedia_title": ""}, {"entity_id": "b", "en_wikipedia_title": "B"}]
    assert title_to_entity(rows) == {"B": "b"}


def test_stage_hour_filters_and_writes_gzip_csv(tmp_path):
    seed = {"Anthropic": "anthropic", "Hugging_Face": "hugging_face"}
    lines = [
        "en Anthropic 10 0",
        "de Anthropic 99 0",
        "en Hugging%20Face 7 0",
        "en Main_Page 500 0",
        "bad line",
    ]
    out = stage_hour("2026-11-02T14:00:00Z", seed, tmp_path, lines=lines)
    assert out.name == "pageviews_20261102-140000.csv.gz"
    with gzip.open(out, "rt", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    assert rows[0] == OUTPUT_FIELDS
    assert rows[1:] == [
        ["anthropic", "Anthropic", "2026-11-02T14:00:00Z", "10"],
        ["hugging_face", "Hugging_Face", "2026-11-02T14:00:00Z", "7"],
    ]


def test_stage_hour_is_idempotent(tmp_path):
    seed = {"Anthropic": "anthropic"}
    lines = ["en Anthropic 10 0"]
    first = stage_hour("2026-11-02T14:00:00Z", seed, tmp_path, lines=lines)
    second = stage_hour("2026-11-02T14:00:00Z", seed, tmp_path, lines=lines)
    assert first == second
    assert sorted(p.name for p in tmp_path.iterdir()) == [first.name]


def test_stage_hour_empty_hour_still_writes_header(tmp_path):
    out = stage_hour("2026-11-02T14:00:00Z", {"Anthropic": "anthropic"}, tmp_path, lines=[])
    with gzip.open(out, "rt", encoding="utf-8") as f:
        assert list(csv.reader(f)) == [OUTPUT_FIELDS]

def test_stage_hour_sums_desktop_and_mobile_views(tmp_path):
    seed = {"Anthropic": "anthropic"}
    lines = [
        "en Anthropic 10 0",
        "en.m Anthropic 25 0",
    ]
    out = stage_hour("2026-11-02T14:00:00Z", seed, tmp_path, lines=lines)
    with gzip.open(out, "rt", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    assert rows[1:] == [["anthropic", "Anthropic", "2026-11-02T14:00:00Z", "35"]]



class _FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_hour_is_published_true_when_file_exists(monkeypatch):
    seen = {}

    def fake_urlopen(req, timeout=None):
        seen["method"] = req.get_method()
        return _FakeResponse()

    monkeypatch.setattr(ingest.urllib.request, "urlopen", fake_urlopen)
    assert ingest.hour_is_published("2026-11-04T11:00:00Z") is True
    assert seen["method"] == "HEAD"


def test_hour_is_published_false_on_404(monkeypatch):
    import urllib.error

    def fake_urlopen(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 404, "Not Found", None, None)

    monkeypatch.setattr(ingest.urllib.request, "urlopen", fake_urlopen)
    assert ingest.hour_is_published("2026-11-04T11:00:00Z") is False


def test_hour_is_published_false_on_server_error_or_network_error(monkeypatch):
    import urllib.error

    def fake_5xx(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 503, "Unavailable", None, None)

    monkeypatch.setattr(ingest.urllib.request, "urlopen", fake_5xx)
    assert ingest.hour_is_published("2026-11-04T11:00:00Z") is False

    def fake_network(req, timeout=None):
        raise urllib.error.URLError("timed out")

    monkeypatch.setattr(ingest.urllib.request, "urlopen", fake_network)
    assert ingest.hour_is_published("2026-11-04T11:00:00Z") is False


def test_hour_is_published_raises_on_other_client_errors(monkeypatch):
    import urllib.error

    def fake_403(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 403, "Forbidden", None, None)

    monkeypatch.setattr(ingest.urllib.request, "urlopen", fake_403)
    with pytest.raises(urllib.error.HTTPError):
        ingest.hour_is_published("2026-11-04T11:00:00Z")

def test_hour_is_published_timeout_counts_as_not_yet(monkeypatch):
    from pageviews_anomaly import ingest

    def timed_out(*args, **kwargs):
        raise TimeoutError("timed out")

    monkeypatch.setattr(ingest.urllib.request, "urlopen", timed_out)
    assert ingest.hour_is_published("2026-11-04T04:00:00Z") is False

