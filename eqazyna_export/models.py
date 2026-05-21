from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ApplicationRecord:
    created_at_raw: str
    document_number: str
    bin_iin: str
    applicant_name: str
    document_type: str
    status: str
    source_url: str

    @property
    def created_at(self) -> Optional[datetime]:
        for fmt in ("%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M", "%d.%m.%Y"):
            try:
                return datetime.strptime(self.created_at_raw.strip(), fmt)
            except Exception:
                continue
        return None

    @property
    def key(self) -> str:
        return f"{self.document_number}|{self.bin_iin}|{self.created_at_raw}"


@dataclass
class CompanyInfo:
    bin_iin: str
    egov_found: bool = False
    egov_status: str = "not_requested"
    egov_name: str = ""
    legal_address: str = ""
    director: str = ""
    activity: str = ""
    region: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)
    error: str = ""
