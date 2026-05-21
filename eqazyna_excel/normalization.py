from __future__ import annotations

import re
import unicodedata


SPACE_RE = re.compile(r"\s+")


def clean_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).replace("\xa0", " ").replace("\u200b", " ").strip()
    text = unicodedata.normalize("NFKC", text)
    text = SPACE_RE.sub(" ", text)
    return text.strip()


def norm_key(value: object) -> str:
    text = clean_text(value).lower().replace("ё", "е")
    return text


def digits_only(value: object) -> str:
    return re.sub(r"\D+", "", clean_text(value))


def is_bin(value: object) -> bool:
    return bool(re.fullmatch(r"\d{12}", digits_only(value)))
