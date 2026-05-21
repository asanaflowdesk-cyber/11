from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any


@dataclass
class ApplicationRecord:
    created_at: datetime | None
    created_at_raw: str
    document_number: str
    applicant_bin: str
    applicant_name: str
    document_type: str
    status: str
    source_url: str
    source_page: int

    @property
    def unique_key(self) -> str:
        return f"{self.document_number}|{self.applicant_bin}|{self.created_at_raw}"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat(sep=" ") if self.created_at else None
        data["unique_key"] = self.unique_key
        return data


@dataclass
class CompanyInfo:
    bin: str
    found: bool = False
    name_ru: str | None = None
    name_kz: str | None = None
    legal_address_ru: str | None = None
    legal_address_kz: str | None = None
    leader_fio: str | None = None
    oked_code: str | None = None
    oked_name_ru: str | None = None
    registration_date: str | None = None
    status: str | None = None
    raw_keys: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
