from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import quote_plus


def collapse_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").replace("\xa0", " ")).strip()


def norm(value: str) -> str:
    return collapse_spaces(value).lower().replace("ё", "е")


def safe_json(value: Any, limit: int = 2000) -> str:
    try:
        text = json.dumps(value, ensure_ascii=False, default=str)
    except Exception:
        text = str(value)
    if len(text) > limit:
        return text[:limit] + "…"
    return text


def first_non_empty(values: Iterable[Any]) -> str:
    for v in values:
        if v is None:
            continue
        text = collapse_spaces(str(v))
        if text:
            return text
    return ""


def flatten_dict(data: Any, prefix: str = "") -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if isinstance(data, dict):
        for k, v in data.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            if isinstance(v, (dict, list)):
                out.update(flatten_dict(v, key))
            else:
                out[key] = v
    elif isinstance(data, list):
        for i, item in enumerate(data):
            out.update(flatten_dict(item, f"{prefix}[{i}]" if prefix else f"[{i}]"))
    return out


def find_by_key_patterns(data: Dict[str, Any], patterns: List[str], min_len: int = 1) -> str:
    flat = flatten_dict(data)
    # сначала ищем по ключам, потом по более слабим совпадениям
    candidates = []
    for key, value in flat.items():
        key_n = norm(key)
        value_s = collapse_spaces(str(value)) if value is not None else ""
        if len(value_s) < min_len:
            continue
        for pattern in patterns:
            if norm(pattern) in key_n:
                candidates.append((len(key_n), value_s))
                break
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1] if candidates else ""


def make_search_links(bin_iin: str, company_name: str, address: str = "") -> Dict[str, str]:
    query = collapse_spaces(f"{bin_iin} {company_name} {address} телефон контакты")
    q = quote_plus(query)
    q2gis = quote_plus(collapse_spaces(f"{bin_iin} {company_name} {address}"))
    return {
        "2gis": f"https://2gis.kz/search/{q2gis}",
        "google": f"https://www.google.com/search?q={q}",
        "yandex": f"https://yandex.kz/search/?text={q}",
    }
