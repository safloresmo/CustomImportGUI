"""
KiCad GitLab - Browse and download symbols from KiCad's official GitLab repositories.

Public API (no authentication required):
  https://gitlab.com/api/v4/projects/kicad%2Flibraries%2Fkicad-symbols/
"""

import re
import sys
import logging
import urllib.request
import urllib.parse
import urllib.error
import ssl
import json
import os
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

GITLAB_API_BASE = "https://gitlab.com/api/v4"
SYMBOLS_PROJECT = "kicad%2Flibraries%2Fkicad-symbols"
SYMBOLS_TREE_URL = f"{GITLAB_API_BASE}/projects/{SYMBOLS_PROJECT}/repository/tree"
SYMBOLS_RAW_URL = f"{GITLAB_API_BASE}/projects/{SYMBOLS_PROJECT}/repository/files/{{path}}/raw"

# Session-level cache
_library_list_cache: Optional[List[Dict]] = None


def _create_ssl_context() -> ssl.SSLContext:
    """Create an SSL context with best-effort certificate handling."""
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
    except Exception:
        pass
    return context


def _get(url: str, timeout: int = 10) -> bytes:
    """Perform a GET request and return raw bytes."""
    ctx = _create_ssl_context()
    req = urllib.request.Request(url, headers={"User-Agent": "CustomImportGUI/1.0"})
    with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
        return resp.read()


def list_symbol_libraries() -> List[Dict]:
    """Return the list of .kicad_sym files available in the official KiCad symbols repo.

    Returns a list of dicts: [{"name": "Amplifier_Audio.kicad_sym", "path": "Amplifier_Audio.kicad_sym"}]
    Result is cached for the lifetime of the Python session.
    """
    global _library_list_cache
    if _library_list_cache is not None:
        return _library_list_cache

    results: List[Dict] = []
    page = 1
    per_page = 100

    try:
        while True:
            url = f"{SYMBOLS_TREE_URL}?ref=master&per_page={per_page}&page={page}"
            data = _get(url)
            entries = json.loads(data)
            if not entries:
                break
            for entry in entries:
                name = entry.get("name", "")
                if name.endswith(".kicad_sym") and entry.get("type") == "blob":
                    results.append({"name": name, "path": entry.get("path", name)})
            if len(entries) < per_page:
                break
            page += 1
    except Exception as e:
        logger.error(f"KiCadGitLab: failed to list symbol libraries: {e}")

    _library_list_cache = results
    return results


def _fetch_library_raw(file_path: str) -> str:
    """Download the raw content of a .kicad_sym file by its path in the repo."""
    encoded_path = urllib.parse.quote(file_path, safe="")
    url = SYMBOLS_RAW_URL.format(path=encoded_path) + "?ref=master"
    data = _get(url)
    return data.decode("utf-8", errors="replace")


def _parse_symbol_names(kicad_sym_content: str) -> List[str]:
    """Extract symbol names from a .kicad_sym file content.

    Looks for top-level symbol entries: (symbol "NAME" ...)
    Excludes derived/unit symbols that contain a slash (unit markers).
    """
    # Match: (symbol "SYMBOL_NAME"  — the name must not contain a slash (unit markers)
    pattern = re.compile(r'^\s*\(symbol\s+"([^"/]+)"\s', re.MULTILINE)
    return pattern.findall(kicad_sym_content)


def search_symbols(query: str, library: str = None) -> List[Dict]:
    """Search for KiCad official symbols.

    Args:
        query: Search term (case-insensitive substring match).
        library: If specified (without .kicad_sym extension), search only within that library.
                 Otherwise, match library names containing the query.

    Returns:
        List of dicts: [{"name": "LM386", "library": "Amplifier_Audio", "description": ""}]
    """
    results: List[Dict] = []
    query_lower = query.lower()

    try:
        if library:
            # Search within a specific library file
            file_path = f"{library}.kicad_sym"
            content = _fetch_library_raw(file_path)
            symbol_names = _parse_symbol_names(content)
            for sym in symbol_names:
                if query_lower in sym.lower():
                    results.append({"name": sym, "library": library, "description": ""})
        else:
            # Match against library names (fast, no file downloads)
            libs = list_symbol_libraries()
            for lib in libs:
                lib_name = lib["name"].replace(".kicad_sym", "")
                if query_lower in lib_name.lower():
                    results.append({"name": lib_name, "library": lib_name, "description": lib["path"]})
    except Exception as e:
        logger.error(f"KiCadGitLab: search_symbols failed: {e}")

    return results


def download_symbol(library_name: str, symbol_name: str, dest_path: str) -> bool:
    """Download a specific symbol from KiCad's official GitLab repo.

    Fetches the full .kicad_sym library file, extracts the requested symbol
    using kiutils, and saves it to dest_path.

    Args:
        library_name: Library name without extension (e.g., "Amplifier_Audio").
        symbol_name: Symbol name within the library (e.g., "LM386").
        dest_path: Destination file path where the symbol will be saved.

    Returns:
        True on success, False on failure.
    """
    try:
        file_path = f"{library_name}.kicad_sym"
        content = _fetch_library_raw(file_path)

        # Setup kiutils path
        current_dir = Path(__file__).resolve().parent
        kiutils_src = current_dir.parent / "kiutils" / "src"
        if str(kiutils_src) not in sys.path:
            sys.path.insert(0, str(kiutils_src))

        from kiutils.symbol import SymbolLib

        # Write content to a temporary file for kiutils to parse
        import tempfile
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".kicad_sym", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            src_lib = SymbolLib.from_file(tmp_path)
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

        # Find the requested symbol
        target_symbol = None
        for sym in src_lib.symbols:
            if sym.entryName == symbol_name:
                target_symbol = sym
                break

        if target_symbol is None:
            logger.error(f"KiCadGitLab: symbol '{symbol_name}' not found in '{library_name}'")
            return False

        dest = Path(dest_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        if dest.exists():
            # Append to existing library
            dest_lib = SymbolLib.from_file(str(dest))
            # Remove if already present
            dest_lib.symbols = [s for s in dest_lib.symbols if s.entryName != symbol_name]
            dest_lib.symbols.append(target_symbol)
            dest_lib.to_file(str(dest))
        else:
            # Create a new library with just this symbol
            new_lib = SymbolLib()
            new_lib.symbols = [target_symbol]
            new_lib.to_file(str(dest))

        logger.info(f"KiCadGitLab: saved '{symbol_name}' from '{library_name}' to '{dest}'")
        return True

    except Exception as e:
        logger.error(f"KiCadGitLab: download_symbol failed: {e}")
        return False
