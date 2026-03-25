"""Internationalization module - loads translations based on system locale."""

import json
import locale
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_locales_dir = Path(__file__).resolve().parent / "locales"
_translations = {}
_current_lang = "en_US"


def _detect_language() -> str:
    """Detect system language, return locale code."""
    try:
        lang, _ = locale.getdefaultlocale()
        if lang and lang.startswith("es"):
            return "es_ES"
    except Exception:
        pass
    return "en_US"


def _load_language(lang: str) -> dict:
    """Load a translation file."""
    path = _locales_dir / f"{lang}.json"
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load translation {lang}: {e}")
    return {}


def init(lang: Optional[str] = None) -> None:
    """Initialize i18n with the given or auto-detected language."""
    global _translations, _current_lang

    if lang is None:
        lang = _detect_language()

    _current_lang = lang
    _translations = _load_language(lang)

    # Fallback to English if needed
    if lang != "en_US" and not _translations:
        _translations = _load_language("en_US")
        _current_lang = "en_US"

    logger.info(f"i18n initialized: {_current_lang}")


def _(key: str, **kwargs) -> str:
    """Get translated string by dot-notation key. Falls back to key itself."""
    if not _translations:
        init()

    # Navigate nested dict with dot notation
    parts = key.split(".")
    value = _translations
    for part in parts:
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return key  # Fallback: return the key

    if isinstance(value, str):
        if kwargs:
            try:
                return value.format(**kwargs)
            except (KeyError, IndexError):
                return value
        return value

    return key


def get_language() -> str:
    """Return current language code."""
    return _current_lang


def set_language(lang: str) -> None:
    """Change language at runtime."""
    init(lang)
