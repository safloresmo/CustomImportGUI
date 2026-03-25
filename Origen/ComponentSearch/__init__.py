"""Component Search - Search EasyEDA/JLCPCB components by keyword."""

import json
import logging
import urllib.request
import urllib.parse
import ssl
import sys
import os
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

JLCPCB_SEARCH_URL = "https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList/v2"
EASYEDA_API_URL = "https://easyeda.com/api/products/{lcsc_id}/components?version=6.4.19.5"


@dataclass
class SearchResult:
    """A single search result."""
    lcsc_id: str
    name: str
    manufacturer: str
    package: str
    category: str
    description: str
    stock: int
    price: float
    image_url: str
    datasheet_url: str
    lcsc_url: str


def _create_ssl_context() -> ssl.SSLContext:
    """Create SSL context with proper certificate handling."""
    context = ssl.create_default_context()
    if sys.platform == "darwin":
        kicad_cert_paths = [
            "/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/certifi/cacert.pem",
            "/Applications/KiCad-10.0/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/certifi/cacert.pem",
        ]
        for cert_path in kicad_cert_paths:
            if os.path.isfile(cert_path):
                try:
                    context.load_verify_locations(cafile=cert_path)
                    return context
                except Exception:
                    pass
    try:
        import certifi
        context.load_verify_locations(cafile=certifi.where())
    except (ImportError, Exception):
        pass
    return context


_ssl_context = _create_ssl_context()


def search_components(keyword: str, page: int = 1, page_size: int = 30) -> List[SearchResult]:
    """Search JLCPCB/LCSC for components by keyword.

    Args:
        keyword: Search term (e.g., "ESP32", "LM7805", "100nF 0402")
        page: Page number (1-based)
        page_size: Results per page (max 100)

    Returns:
        List of SearchResult objects
    """
    if not keyword or not keyword.strip():
        return []

    payload = json.dumps({
        "keyword": keyword.strip(),
        "pageSize": min(page_size, 100),
        "currentPage": page,
    }).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "CustomImportGUI/1.0",
        "Accept": "application/json",
    }

    try:
        req = urllib.request.Request(JLCPCB_SEARCH_URL, data=payload, headers=headers)
        with urllib.request.urlopen(req, timeout=15, context=_ssl_context) as response:
            raw = response.read()
            if raw[:2] == b"\x1f\x8b":
                import gzip
                data = json.loads(gzip.decompress(raw))
            else:
                data = json.loads(raw)
    except Exception as e:
        logger.error(f"Search request failed: {e}")
        return []

    results = []
    try:
        items = data.get("data", {}).get("componentPageInfo", {}).get("list", [])
        for item in items:
            # Image will be fetched on-demand from EasyEDA API
            image_url = ""  # Populated lazily via get_component_image()

            # Get first price
            prices = item.get("componentPrices", [])
            price = prices[0].get("productPrice", 0) if prices else 0

            results.append(SearchResult(
                lcsc_id=item.get("componentCode", ""),
                name=item.get("componentModelEn", "") or item.get("componentName", ""),
                manufacturer=item.get("componentBrandEn", ""),
                package=item.get("componentSpecificationEn", ""),
                category=item.get("componentTypeEn", ""),
                description=item.get("describe", "")[:200],
                stock=item.get("stockCount", 0),
                price=price,
                image_url=image_url,
                datasheet_url=item.get("dataManualUrl", ""),
                lcsc_url=item.get("lcscGoodsUrl", ""),
            ))
    except Exception as e:
        logger.error(f"Failed to parse search results: {e}")

    return results


def get_search_total(keyword: str) -> int:
    """Get total number of results for a keyword."""
    payload = json.dumps({
        "keyword": keyword.strip(),
        "pageSize": 1,
        "currentPage": 1,
    }).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "CustomImportGUI/1.0",
        "Accept": "application/json",
    }

    try:
        req = urllib.request.Request(JLCPCB_SEARCH_URL, data=payload, headers=headers)
        with urllib.request.urlopen(req, timeout=10, context=_ssl_context) as response:
            data = json.loads(response.read())
        return data.get("data", {}).get("componentPageInfo", {}).get("total", 0)
    except Exception:
        return 0


def fetch_component_image(lcsc_id: str) -> Optional[bytes]:
    """Fetch component thumbnail image from EasyEDA API. Returns raw PNG bytes or None."""
    if not lcsc_id:
        return None

    try:
        # Get component data from EasyEDA to find thumb URL
        headers = {
            "User-Agent": "CustomImportGUI/1.0",
            "Accept": "application/json",
        }
        url = EASYEDA_API_URL.format(lcsc_id=lcsc_id)
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10, context=_ssl_context) as response:
            data = json.loads(response.read())

        # Extract thumb URL
        result = data.get("result", {})
        if isinstance(result, list) and result:
            result = result[0]

        thumb = result.get("thumb", "")
        if not thumb:
            return None

        # Fix protocol-relative URL
        if thumb.startswith("//"):
            thumb = "https:" + thumb

        # Download the image
        req = urllib.request.Request(thumb, headers={"User-Agent": "CustomImportGUI/1.0"})
        with urllib.request.urlopen(req, timeout=10, context=_ssl_context) as response:
            if response.status == 200:
                return response.read()

    except Exception as e:
        logger.debug(f"Failed to fetch image for {lcsc_id}: {e}")

    return None
