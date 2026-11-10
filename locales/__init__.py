from locales.en import EN_STRINGS
from locales.hi import HI_STRINGS
from locales.hinglish import HINGLISH_STRINGS

STRINGS = {
    "en": EN_STRINGS,
    "hi": HI_STRINGS,
    "hinglish": HINGLISH_STRINGS
}

def escape_md(val):
    if isinstance(val, str):
        return val.replace("_", "\\_")
    return val

def get_text(lang_code: str, key: str, **kwargs) -> str:
    lang = lang_code if lang_code in STRINGS else "en"
    text_dict = STRINGS.get(lang, EN_STRINGS)
    template = text_dict.get(key, EN_STRINGS.get(key, f"[{key}]"))
    if kwargs:
        escaped_kwargs = {k: escape_md(v) for k, v in kwargs.items()}
        try:
            return template.format(**escaped_kwargs)
        except Exception:
            return template
    return template
