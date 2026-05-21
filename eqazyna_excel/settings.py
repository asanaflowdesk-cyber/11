from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _bool(value: str | None, default: bool = True) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "да"}


@dataclass(frozen=True)
class Settings:
    eqazyna_base_url: str
    egov_api_key: str | None
    export_dir: Path
    request_timeout_sec: int
    request_delay_sec: float
    user_agent: str
    verify_ssl: bool
    max_retries: int
    egov_dataset: str
    egov_version: str


def load_settings(env_path: str | Path | None = None) -> Settings:
    if env_path:
        load_dotenv(env_path)
    else:
        load_dotenv(PROJECT_ROOT / ".env")

    export_dir_raw = os.getenv("EXPORT_DIR", "exports")
    export_dir = Path(export_dir_raw)
    if not export_dir.is_absolute():
        export_dir = PROJECT_ROOT / export_dir

    return Settings(
        eqazyna_base_url=os.getenv(
            "EQAZYNA_BASE_URL",
            "https://minerals.e-qazyna.kz/ru/guest/reestr/doc/list",
        ),
        egov_api_key=os.getenv("EGOV_API_KEY") or None,
        export_dir=export_dir,
        request_timeout_sec=int(os.getenv("REQUEST_TIMEOUT_SEC", "30")),
        request_delay_sec=float(os.getenv("REQUEST_DELAY_SEC", "0.8")),
        user_agent=os.getenv(
            "USER_AGENT",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/125.0 Safari/537.36 eQazynaExcelExporter/1.0",
        ),
        verify_ssl=_bool(os.getenv("VERIFY_SSL"), True),
        max_retries=int(os.getenv("MAX_RETRIES", "3")),
        egov_dataset=os.getenv("EGOV_DATASET", "gbd_ul"),
        egov_version=os.getenv("EGOV_VERSION", "v1"),
    )
