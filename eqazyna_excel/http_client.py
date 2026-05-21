from __future__ import annotations

import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .settings import Settings


def make_session(settings: Settings) -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": settings.user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.7",
        "Connection": "keep-alive",
    })
    retry = Retry(
        total=settings.max_retries,
        connect=settings.max_retries,
        read=settings.max_retries,
        status=settings.max_retries,
        backoff_factor=0.8,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def get_text(session: requests.Session, url: str, settings: Settings, params: dict[str, Any] | None = None) -> str:
    response = session.get(url, params=params, timeout=settings.request_timeout_sec, verify=settings.verify_ssl)
    response.raise_for_status()
    if settings.request_delay_sec > 0:
        time.sleep(settings.request_delay_sec)
    return response.text


def get_json(session: requests.Session, url: str, settings: Settings, params: dict[str, Any] | None = None) -> Any:
    response = session.get(url, params=params, timeout=settings.request_timeout_sec, verify=settings.verify_ssl)
    response.raise_for_status()
    if settings.request_delay_sec > 0:
        time.sleep(settings.request_delay_sec)
    return response.json()
