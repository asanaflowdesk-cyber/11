from __future__ import annotations

import json
import time
from typing import Any, Dict, Iterable, List, Optional

import requests

from .models import CompanyInfo
from .utils import collapse_spaces, find_by_key_patterns, safe_json

DEFAULT_ENDPOINT = "https://data.egov.kz/api/v4/gbd_ul/v1"


def _extract_items(payload: Any) -> List[Dict[str, Any]]:
    """Портал data.egov.kz может менять оболочку ответа; вытаскиваем записи максимально терпимо."""
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if not isinstance(payload, dict):
        return []

    for key in ("data", "items", "results", "result", "records", "hits"):
        value = payload.get(key)
        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]
        if isinstance(value, dict):
            # Elasticsearch-like: hits.hits[*]._source
            inner_hits = value.get("hits")
            if isinstance(inner_hits, list):
                out = []
                for h in inner_hits:
                    if isinstance(h, dict):
                        out.append(h.get("_source") if isinstance(h.get("_source"), dict) else h)
                return out

    # Elasticsearch-like верхнего уровня.
    hits = payload.get("hits")
    if isinstance(hits, dict) and isinstance(hits.get("hits"), list):
        out = []
        for h in hits["hits"]:
            if isinstance(h, dict):
                out.append(h.get("_source") if isinstance(h.get("_source"), dict) else h)
        return out

    # Иногда API может вернуть одну запись объектом.
    if any(k.lower() in ("bin", "iin", "iinbin") for k in payload.keys()):
        return [payload]

    return []


def _build_sources(bin_iin: str) -> Iterable[Dict[str, Any]]:
    # Сначала строгие варианты, потом широкий query_string. Поля в наборе могут называться по-разному.
    yield {
        "size": 5,
        "query": {
            "bool": {
                "should": [
                    {"match": {"bin": bin_iin}},
                    {"match": {"BIN": bin_iin}},
                    {"match": {"БИН": bin_iin}},
                    {"term": {"bin.keyword": bin_iin}},
                    {"term": {"BIN.keyword": bin_iin}},
                    {"term": {"БИН.keyword": bin_iin}},
                ],
                "minimum_should_match": 1,
            }
        },
    }
    yield {"size": 5, "query": {"query_string": {"query": bin_iin}}}


def query_company(bin_iin: str, api_key: str, endpoint: str = DEFAULT_ENDPOINT, timeout: int = 40) -> CompanyInfo:
    info = CompanyInfo(bin_iin=bin_iin, egov_status="not_found")
    if not api_key:
        info.egov_status = "skipped_no_api_key"
        return info

    session = requests.Session()
    session.headers.update({"User-Agent": "eQazynaExcelExporter/1.0"})
    last_error = ""

    for source in _build_sources(bin_iin):
        params = {"apiKey": api_key, "source": json.dumps(source, ensure_ascii=False)}
        try:
            response = session.get(endpoint, params=params, timeout=timeout)
            if response.status_code == 401 or response.status_code == 403:
                return CompanyInfo(bin_iin=bin_iin, egov_status="auth_error", error="eGov API key rejected")
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:  # noqa: BLE001 - нужен понятный Excel-статус, а не падение всей выгрузки
            last_error = str(exc)
            continue

        items = _extract_items(payload)
        if not items:
            continue

        # Берём запись, где явно встречается БИН; если не нашли — первую.
        chosen = items[0]
        for item in items:
            if bin_iin in safe_json(item, limit=10000):
                chosen = item
                break
        return normalize_company(bin_iin, chosen)

    info.error = last_error
    return info


def normalize_company(bin_iin: str, raw: Dict[str, Any]) -> CompanyInfo:
    name = find_by_key_patterns(
        raw,
        [
            "name_ru",
            "nameRus",
            "naimenovanie",
            "наименование",
            "nazvanie",
            "full_name",
            "fullName",
            "org_name",
            "organization",
            "name",
        ],
        min_len=2,
    )
    address = find_by_key_patterns(
        raw,
        [
            "legal_address",
            "jur_address",
            "юр",
            "yur",
            "address",
            "адрес",
            "mesto",
            "location",
            "kato",
        ],
        min_len=5,
    )
    director = find_by_key_patterns(
        raw,
        ["director", "rukovod", "руковод", "chairman", "fio", "fullname", "басш", "head"],
        min_len=5,
    )
    activity = find_by_key_patterns(
        raw,
        ["oked", "окэд", "activity", "вид", "deyatel", "economic", "сфера"],
        min_len=2,
    )

    return CompanyInfo(
        bin_iin=bin_iin,
        egov_found=True,
        egov_status="found",
        egov_name=collapse_spaces(name),
        legal_address=collapse_spaces(address),
        director=collapse_spaces(director),
        activity=collapse_spaces(activity),
        raw=raw,
    )


def enrich_many(bin_values: Iterable[str], api_key: str, sleep_seconds: float = 0.25) -> Dict[str, CompanyInfo]:
    out: Dict[str, CompanyInfo] = {}
    for i, bin_iin in enumerate(dict.fromkeys(bin_values).keys(), start=1):
        out[bin_iin] = query_company(bin_iin, api_key=api_key)
        if sleep_seconds and i % 5 == 0:
            time.sleep(sleep_seconds)
    return out
