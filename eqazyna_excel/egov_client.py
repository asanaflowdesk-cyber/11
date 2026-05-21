from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import requests

from .http_client import get_json
from .models import CompanyInfo
from .normalization import clean_text, digits_only, norm_key
from .settings import Settings


def _pick(data: Mapping[str, Any], candidates: list[str]) -> str | None:
    if not data:
        return None
    lower_map = {norm_key(k): k for k in data.keys()}
    for candidate in candidates:
        key = lower_map.get(norm_key(candidate))
        if key is not None:
            value = clean_text(data.get(key))
            if value:
                return value
    # fallback by substring, because gbd_ul field names may shift between versions
    for candidate in candidates:
        c = norm_key(candidate)
        for lk, original in lower_map.items():
            if c in lk:
                value = clean_text(data.get(original))
                if value:
                    return value
    return None


def _extract_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        # Some endpoints wrap records into rows/items/data.
        for key in ("data", "rows", "items", "result", "hits"):
            value = payload.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
            if isinstance(value, dict):
                # Elasticsearch style: hits.hits._source
                hits = value.get("hits")
                if isinstance(hits, list):
                    out = []
                    for hit in hits:
                        if isinstance(hit, dict):
                            src = hit.get("_source") if isinstance(hit.get("_source"), dict) else hit
                            out.append(src)
                    return out
        # Single object can be returned.
        if any(norm_key(k) in {"bin", "бин"} for k in payload.keys()):
            return [payload]
    return []


class EgovClient:
    def __init__(self, settings: Settings, session: requests.Session):
        self.settings = settings
        self.session = session
        self.base_url = f"https://data.egov.kz/api/v4/{settings.egov_dataset}/{settings.egov_version}"

    def get_company_by_bin(self, bin_number: str) -> CompanyInfo:
        bin_number = digits_only(bin_number)
        if not self.settings.egov_api_key:
            return CompanyInfo(bin=bin_number, found=False, error="EGOV_API_KEY is not set")
        if len(bin_number) != 12:
            return CompanyInfo(bin=bin_number, found=False, error="BIN must contain 12 digits")

        attempts = [
            {"size": 1, "query": {"bool": {"must": [{"match": {"bin": bin_number}}]}}},
            {"size": 1, "query": {"bool": {"must": [{"term": {"bin": bin_number}}]}}},
            {"size": 1, "query": {"bool": {"should": [{"match": {"bin": bin_number}}, {"prefix": {"bin": bin_number}}]}}},
        ]
        last_error: str | None = None
        for source in attempts:
            try:
                payload = get_json(
                    self.session,
                    self.base_url,
                    self.settings,
                    params={
                        "apiKey": self.settings.egov_api_key,
                        "source": json.dumps(source, ensure_ascii=False),
                    },
                )
                records = _extract_records(payload)
                if not records:
                    continue
                chosen = self._choose_record(records, bin_number)
                if chosen:
                    return self._to_company_info(bin_number, chosen)
            except Exception as exc:  # noqa: BLE001 - surface API error to Excel, don't kill full export.
                last_error = f"{type(exc).__name__}: {exc}"
        return CompanyInfo(bin=bin_number, found=False, error=last_error or "Not found in gbd_ul")

    def _choose_record(self, records: list[dict[str, Any]], bin_number: str) -> dict[str, Any] | None:
        for record in records:
            record_bin = digits_only(_pick(record, ["bin", "БИН", "iinbin", "iin_bin", "business_identification_number"]) or "")
            if record_bin == bin_number:
                return record
        return records[0] if records else None

    def _to_company_info(self, bin_number: str, record: dict[str, Any]) -> CompanyInfo:
        # Candidate lists intentionally broad: the open dataset schema has changed before.
        name_ru = _pick(record, [
            "nameru", "name_ru", "nameRu", "name", "nam", "Наименование на русском", "Наименование", "org_name_ru",
            "full_name_ru", "fullNameRu",
        ])
        name_kz = _pick(record, [
            "namekz", "name_kz", "nameKz", "Наименование на казахском", "org_name_kz", "full_name_kz", "fullNameKz",
        ])
        legal_address_ru = _pick(record, [
            "addressru", "address_ru", "addressRu", "legal_address", "legal_address_ru", "legalAddressRu", "Юридический адрес",
            "Адрес", "address", "jur_address", "jurAddress", "full_address_ru",
        ])
        legal_address_kz = _pick(record, [
            "addresskz", "address_kz", "addressKz", "legal_address_kz", "legalAddressKz", "full_address_kz",
        ])
        leader_fio = _pick(record, [
            "fio", "leader", "leader_fio", "rukovoditel", "Руководитель", "ФИО руководителя", "boss", "director",
            "full_name_boss", "fio_rukovoditel",
        ])
        oked_code = _pick(record, ["oked", "oked_code", "okved", "Код ОКЭД", "okedCode"])
        oked_name_ru = _pick(record, ["oked_name", "oked_name_ru", "ОКЭД", "Вид деятельности", "okedNameRu"])
        registration_date = _pick(record, [
            "registration_date", "reg_date", "date_reg", "Дата регистрации", "registerDate", "regDate",
        ])
        status = _pick(record, ["status", "Статус", "active", "Статус юрлица"])

        return CompanyInfo(
            bin=bin_number,
            found=True,
            name_ru=name_ru,
            name_kz=name_kz,
            legal_address_ru=legal_address_ru,
            legal_address_kz=legal_address_kz,
            leader_fio=leader_fio,
            oked_code=oked_code,
            oked_name_ru=oked_name_ru,
            registration_date=registration_date,
            status=status,
            raw_keys=", ".join(sorted(record.keys())),
        )
