from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import List, Sequence

from .egov_client import enrich_many
from .exporter import write_excel
from .models import ApplicationRecord
from .region import detect_region
from .scraper import DEFAULT_DOC_TYPE, DEFAULT_STATUSES, filter_records, scrape_applications


def run_export(
    pages: int = 5,
    output_path: str | Path = "exports/eqazyna_export.xlsx",
    doc_type: str = DEFAULT_DOC_TYPE,
    statuses: Sequence[str] = DEFAULT_STATUSES,
    use_egov: bool = True,
    egov_api_key: str | None = None,
) -> Path:
    records_all = scrape_applications(pages=pages)
    records = filter_records(records_all, doc_type=doc_type, statuses=statuses)

    companies = {}
    if use_egov:
        key = egov_api_key if egov_api_key is not None else os.getenv("EGOV_API_KEY", "")
        companies = enrich_many((r.bin_iin for r in records), api_key=key)
        for company in companies.values():
            company.region = detect_region(company.legal_address)

    output = write_excel(records, companies, output_path=output_path, generated_at=datetime.now())
    return output
