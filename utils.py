import json
from pathlib import Path

_TRANSLATIONS = None


def _load():
    global _TRANSLATIONS
    if _TRANSLATIONS is None:
        path = Path(__file__).parent / "locales" / "translations.json"
        with open(path, "r", encoding="utf-8") as f:
            _TRANSLATIONS = json.load(f)
    return _TRANSLATIONS


def T(lang, *keys):
    """Return a translated string.  Usage: T("fr", "nav", "about")"""
    t = _load()
    val = t.get(lang, t.get("en", {}))
    for k in keys:
        if isinstance(val, dict) and k in val:
            val = val[k]
        else:
            # Fall back to English
            en = t.get("en", {})
            for ek in keys:
                if isinstance(en, dict) and ek in en:
                    en = en[ek]
                else:
                    return f"[{'.'.join(keys)}]"
            return en
    return val
