"""Tests for ComponentSearch - SearchResult dataclass, URL construction, and HTTP mocking."""

import json
import gzip
import pytest
from unittest.mock import patch, MagicMock
from ComponentSearch import (
    SearchResult,
    search_components,
    JLCPCB_SEARCH_URL,
    EASYEDA_API_URL,
    fetch_component_image,
)


# ---------------------------------------------------------------------------
# SearchResult dataclass
# ---------------------------------------------------------------------------

def test_search_result_fields():
    result = SearchResult(
        lcsc_id="C14663",
        name="ESP32-WROOM-32",
        manufacturer="Espressif",
        package="SMD",
        category="WiFi Modules",
        description="WiFi+BT module",
        stock=1000,
        price=3.50,
        image_url="https://example.com/img.png",
        datasheet_url="https://example.com/ds.pdf",
        lcsc_url="https://lcsc.com/product-detail/C14663.html",
    )
    assert result.lcsc_id == "C14663"
    assert result.name == "ESP32-WROOM-32"
    assert result.manufacturer == "Espressif"
    assert result.package == "SMD"
    assert result.category == "WiFi Modules"
    assert result.description == "WiFi+BT module"
    assert result.stock == 1000
    assert result.price == 3.50


def test_search_result_is_dataclass():
    """SearchResult should support equality comparison via dataclass."""
    r1 = SearchResult("C1", "A", "M", "P", "C", "D", 0, 0.0, "", "", "")
    r2 = SearchResult("C1", "A", "M", "P", "C", "D", 0, 0.0, "", "", "")
    assert r1 == r2


# ---------------------------------------------------------------------------
# Empty / whitespace keyword returns early
# ---------------------------------------------------------------------------

def test_empty_keyword_returns_empty_list():
    assert search_components("") == []


def test_whitespace_keyword_returns_empty_list():
    assert search_components("   ") == []


# ---------------------------------------------------------------------------
# Mocked HTTP - successful response
# ---------------------------------------------------------------------------

def _make_jlcpcb_response(items):
    """Build a minimal JLCPCB API JSON payload."""
    return json.dumps({
        "data": {
            "componentPageInfo": {
                "list": items,
                "total": len(items),
            }
        }
    }).encode("utf-8")


def _mock_urlopen(raw_bytes):
    """Return a context-manager mock that yields raw_bytes on .read()."""
    mock_response = MagicMock()
    mock_response.read.return_value = raw_bytes
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


SAMPLE_ITEM = {
    "componentCode": "C14663",
    "componentModelEn": "ESP32-WROOM-32",
    "componentName": "ESP32",
    "componentBrandEn": "Espressif",
    "componentSpecificationEn": "SMD",
    "componentTypeEn": "WiFi Modules",
    "describe": "WiFi+BT module",
    "stockCount": 500,
    "componentPrices": [{"productPrice": 3.50}],
    "dataManualUrl": "https://example.com/ds.pdf",
    "lcscGoodsUrl": "https://lcsc.com/C14663",
}


def test_search_components_parses_single_result(monkeypatch):
    raw = _make_jlcpcb_response([SAMPLE_ITEM])

    with patch("urllib.request.urlopen", return_value=_mock_urlopen(raw)):
        results = search_components("ESP32")

    assert len(results) == 1
    r = results[0]
    assert r.lcsc_id == "C14663"
    assert r.name == "ESP32-WROOM-32"
    assert r.manufacturer == "Espressif"
    assert r.stock == 500
    assert r.price == 3.50


def test_search_components_parses_multiple_results(monkeypatch):
    items = [dict(SAMPLE_ITEM, componentCode=f"C{i}") for i in range(5)]
    raw = _make_jlcpcb_response(items)

    with patch("urllib.request.urlopen", return_value=_mock_urlopen(raw)):
        results = search_components("chip")

    assert len(results) == 5


def test_search_components_handles_empty_list(monkeypatch):
    raw = _make_jlcpcb_response([])

    with patch("urllib.request.urlopen", return_value=_mock_urlopen(raw)):
        results = search_components("nothing")

    assert results == []


def test_search_components_handles_missing_prices(monkeypatch):
    item = dict(SAMPLE_ITEM, componentPrices=[])
    raw = _make_jlcpcb_response([item])

    with patch("urllib.request.urlopen", return_value=_mock_urlopen(raw)):
        results = search_components("ESP32")

    assert results[0].price == 0


def test_search_components_truncates_long_description(monkeypatch):
    item = dict(SAMPLE_ITEM, describe="x" * 300)
    raw = _make_jlcpcb_response([item])

    with patch("urllib.request.urlopen", return_value=_mock_urlopen(raw)):
        results = search_components("ESP32")

    assert len(results[0].description) <= 200


def test_search_components_handles_gzip_response(monkeypatch):
    raw_json = _make_jlcpcb_response([SAMPLE_ITEM])
    compressed = gzip.compress(raw_json)

    with patch("urllib.request.urlopen", return_value=_mock_urlopen(compressed)):
        results = search_components("ESP32")

    assert len(results) == 1
    assert results[0].lcsc_id == "C14663"


# ---------------------------------------------------------------------------
# Mocked HTTP - error handling
# ---------------------------------------------------------------------------

def test_search_components_returns_empty_on_network_error(monkeypatch):
    with patch("urllib.request.urlopen", side_effect=Exception("network down")):
        results = search_components("ESP32")
    assert results == []


def test_search_components_returns_empty_on_malformed_json(monkeypatch):
    mock_response = _mock_urlopen(b"not json at all {{{")

    with patch("urllib.request.urlopen", return_value=mock_response):
        results = search_components("ESP32")

    assert results == []


# ---------------------------------------------------------------------------
# fetch_component_image
# ---------------------------------------------------------------------------

def test_fetch_component_image_empty_id_returns_none():
    assert fetch_component_image("") is None


def test_fetch_component_image_returns_bytes_on_success(monkeypatch):
    easyeda_payload = json.dumps({
        "result": [{"thumb": "//example.com/img.png"}]
    }).encode("utf-8")
    image_bytes = b"\x89PNG\r\n\x1a\n"  # minimal PNG header

    call_count = 0

    def fake_urlopen(req, timeout=None, context=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _mock_urlopen(easyeda_payload)
        mock = _mock_urlopen(image_bytes)
        mock.status = 200
        return mock

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        result = fetch_component_image("C14663")

    assert result == image_bytes


def test_fetch_component_image_returns_none_on_error(monkeypatch):
    with patch("urllib.request.urlopen", side_effect=Exception("timeout")):
        result = fetch_component_image("C14663")
    assert result is None
