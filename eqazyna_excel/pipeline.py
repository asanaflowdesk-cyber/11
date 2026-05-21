from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

from .egov_client import EgovClient
from .http_client import get_text, make_session
from .models import ApplicationRecord, CompanyInfo
from .normalization import clean_text
from .region import detect_region, load_regions
from .scraper import build_page_url, filter_applications, parse_applications
from .search_links import dgis_search_url, google_search_url, make_search_query, yandex_search_url
from .settings import Settings


def collect_records(settings: Settings, pages: int, document_type: str, statuses: Iterable[str]) -> list[ApplicationRecord]:
    session = make_session(settings)
    all_records: list[ApplicationRecord] = []
    for page in range(1, pages + 1):
        url = build_page_url(settings.eqazyna_base_url, page)
        html = get_text(session, url, settings)
        parsed = parse_applications(html, source_url=url, source_page=page)
        all_records.extend(parsed)
    filtered = filter_applications(all_records, document_type=document_type, statuses=statuses)
    return filtered


def enrich_records(
    records: list[ApplicationRecord],
    settings: Settings,
    regions_path: str | Path,
    use_egov: bool = True,
) -> list[dict]:
    regions = load_regions(regions_path)
    session = make_session(settings)
    egov = EgovClient(settings, session)
    cache: dict[str, CompanyInfo] = {}
    exported_at = datetime.now()
    rows: list[dict] = []

    for rec in records:
        company = CompanyInfo(bin=rec.applicant_bin, found=False, error="eGov disabled")
        if use_egov:
            if rec.applicant_bin not in cache:
                cache[rec.applicant_bin] = egov.get_company_by_bin(rec.applicant_bin)
            company = cache[rec.applicant_bin]

        address_for_region = company.legal_address_ru or company.legal_address_kz
        region = detect_region(address_for_region, regions)
        display_company_name = company.name_ru or rec.applicant_name
        query = make_search_query(rec.applicant_bin, display_company_name, address_for_region)

        rows.append({
            "exported_at": exported_at,
            "created_at": rec.created_at,
            "document_number": rec.document_number,
            "applicant_bin": rec.applicant_bin,
            "applicant_name": rec.applicant_name,
            "document_type": rec.document_type,
            "status": rec.status,
            "egov_found": "Да" if company.found else "Нет",
            "egov_name_ru": company.name_ru,
            "egov_name_kz": company.name_kz,
            "legal_address_ru": company.legal_address_ru,
            "legal_address_kz": company.legal_address_kz,
            "region": region.region_name,
            "region_confidence": region.confidence,
            "leader_fio": company.leader_fio,
            "oked_code": company.oked_code,
            "oked_name_ru": company.oked_name_ru,
            "registration_date": company.registration_date,
            "company_status": company.status,
            "egov_error": company.error,
            "search_2gis": dgis_search_url(query),
            "search_google": google_search_url(query),
            "search_yandex": yandex_search_url(query),
            "source_page": rec.source_page,
            "source_url": rec.source_url,
            "unique_key": rec.unique_key,
        })
    return rows
