"""Backend translations — loaded from JSON language files (locales/).

Each message is a `str.format` template: interpolated values are passed as
named parameters, e.g. ``t("fr", "rsid.oversold", rsi_daily=28.4)``.
English ("en") is the default, French ("fr") the secondary fallback.
"""
import json
import os

_LOCALES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locales")
_DEFAULT = "en"
_SUPPORTED = ("en", "fr")
_cache: dict[str, dict[str, str]] = {}


def _load(lang: str) -> dict[str, str]:
    if lang not in _cache:
        path = os.path.join(_LOCALES_DIR, f"{lang}.json")
        with open(path, encoding="utf-8") as f:
            _cache[lang] = json.load(f)
    return _cache[lang]


def normalize(lang: str) -> str:
    """Return a supported language (English fallback)."""
    return lang if lang in _SUPPORTED else _DEFAULT


def t(lang: str, key: str, **params) -> str:
    """Translate `key` in `lang` and interpolate `params` (via str.format)."""
    lang = normalize(lang)
    template = _load(lang).get(key)
    if template is None:                     # English fallback then raw key
        template = _load(_DEFAULT).get(key, key)
    return template.format(**params) if params else template
