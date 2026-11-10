import logging
import urllib.error

import pytest

from pageviews_anomaly import ingest

HOUR = "2026-11-07T13:00:00Z"


class _Response:
    """Stands in for the object urlopen returns, so 'with' works."""
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _http_error(code):
    return urllib.error.HTTPError(url="x", code=code, msg="test", hdrs=None, fp=None)


def _patch_urlopen(monkeypatch, result):
    """Make urlopen either return a response or raise the given exception."""
    def fake_urlopen(*args, **kwargs):
        if isinstance(result, BaseException):
            raise result
        return _Response()
    monkeypatch.setattr(ingest.urllib.request, "urlopen", fake_urlopen)


def test_published_returns_true_and_logs(monkeypatch, caplog):
    _patch_urlopen(monkeypatch, None)
    with caplog.at_level(logging.INFO, logger="pageviews_anomaly.ingest"):
        assert ingest.hour_is_published(HOUR) is True
    assert "is published" in caplog.text


def test_404_returns_false_and_logs_info(monkeypatch, caplog):
    _patch_urlopen(monkeypatch, _http_error(404))
    with caplog.at_level(logging.INFO, logger="pageviews_anomaly.ingest"):
        assert ingest.hour_is_published(HOUR) is False
    assert "not published yet" in caplog.text


def test_500_returns_false_and_logs_warning(monkeypatch, caplog):
    _patch_urlopen(monkeypatch, _http_error(500))
    with caplog.at_level(logging.WARNING, logger="pageviews_anomaly.ingest"):
        assert ingest.hour_is_published(HOUR) is False
    assert "HTTP 500" in caplog.text


def test_429_returns_false_and_logs_warning(monkeypatch, caplog):
    _patch_urlopen(monkeypatch, _http_error(429))
    with caplog.at_level(logging.WARNING, logger="pageviews_anomaly.ingest"):
        assert ingest.hour_is_published(HOUR) is False
    assert "HTTP 429" in caplog.text


def test_network_error_returns_false_and_logs_warning(monkeypatch, caplog):
    _patch_urlopen(monkeypatch, urllib.error.URLError("no route to host"))
    with caplog.at_level(logging.WARNING, logger="pageviews_anomaly.ingest"):
        assert ingest.hour_is_published(HOUR) is False
    assert "check failed" in caplog.text


def test_403_raises(monkeypatch):
    _patch_urlopen(monkeypatch, _http_error(403))
    with pytest.raises(urllib.error.HTTPError):
        ingest.hour_is_published(HOUR)