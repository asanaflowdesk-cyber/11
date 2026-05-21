from __future__ import annotations

import re
import time
from typing import Iterable, List, Sequence
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

from .models import ApplicationRecord
from .utils import collapse_spaces, norm

BASE_URL = "https://minerals.e-qazyna.kz/ru/guest/reestr/doc/list"

DEFAULT_DOC_TYPE = "Заявка на разведку ТПИ"
DEFAULT_STATUSES = ("Отправлено на рассмотрение", "Принято")

KNOWN_STATUSES = (
    "Отправлено на рассмотрение",
    "Принято",
    "Выдана лицензия",
    "Отклонено",
    "Отозвано",
    "Аннулировано",
    "Завершено",
)

# Используется только fallback-парсером, если сайт отдаст не табличный HTML.
KNOWN_DOC_TYPES = (
    "Заявка на разведку ТПИ",
    "Заявка на продление лицензии на разведку ТПИ",
    "Заявка на добычу ТПИ",
    "Заявка на разведку и добычу",
    "Оцифровка контракта",
    "Оцифровка лицензии ТПИ",
    "Переход на лицензионный режим",
    "Миграция лицензии на разведку ТПИ",
    "Миграция лицензии на добычу ТПИ",
    "Миграция контракта на разведку ТПИ",
    "Миграция контракта на добычу ТПИ",
    "Регистрация договора залога ТПИ",
    "Регистрация договора залога ОПИ",
    "Отчетность ЛКУ",
    "Заключение об отсутствии полезных ископаемых",
    "Выдача лицензии на экспорт информации",
    "Геологическое изучение недр",
    "Горный/Геологический отвод",
)


def page_url(page: int) -> str:
    if page <= 1:
        return BASE_URL
    return f"{BASE_URL}?{urlencode({'p': page})}"


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (compatible; eQazynaExportBot/1.0; +https://github.com/)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.7",
        }
    )
    return session


def fetch_page(session: requests.Session, page: int, timeout: int = 30) -> str:
    url = page_url(page)
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text


def parse_html_page(html: str, source_url: str) -> List[ApplicationRecord]:
    soup = BeautifulSoup(html, "lxml")
    records = _parse_tables(soup, source_url)
    if records:
        return records
    return _parse_text_fallback(soup.get_text("\n", strip=True), source_url)


def _parse_tables(soup: BeautifulSoup, source_url: str) -> List[ApplicationRecord]:
    records: List[ApplicationRecord] = []
    for tr in soup.select("tr"):
        cells = [collapse_spaces(c.get_text(" ", strip=True)) for c in tr.find_all(["td", "th"])]
        if len(cells) < 6:
            continue
        if norm(cells[0]).startswith("дата создания"):
            continue
        created, doc_no, bin_iin, applicant, doc_type, status = cells[:6]
        if not re.search(r"\d{2}\.\d{2}\.\d{4}", created):
            continue
        if not re.fullmatch(r"\d{12}", re.sub(r"\D", "", bin_iin)):
            continue
        records.append(
            ApplicationRecord(
                created_at_raw=created,
                document_number=doc_no,
                bin_iin=re.sub(r"\D", "", bin_iin),
                applicant_name=applicant,
                document_type=doc_type,
                status=status,
                source_url=source_url,
            )
        )
    return records


def _parse_text_fallback(text: str, source_url: str) -> List[ApplicationRecord]:
    records: List[ApplicationRecord] = []
    lines = [collapse_spaces(x) for x in text.splitlines() if collapse_spaces(x)]
    line_re = re.compile(
        r"(?P<created>\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}:\d{2})\s+"
        r"(?P<doc>\d{3,}-[A-ZА-Я]+)\s+"
        r"(?P<bin>\d{12})\s+"
        r"(?P<rest>.+)$"
    )
    for line in lines:
        match = line_re.search(line)
        if not match:
            continue
        rest = match.group("rest")
        status = _find_status_at_end(rest)
        if not status:
            continue
        before_status = collapse_spaces(rest[: -len(status)])
        doc_type = _find_doc_type(before_status)
        if not doc_type:
            continue
        applicant = collapse_spaces(before_status.split(doc_type, 1)[0])
        records.append(
            ApplicationRecord(
                created_at_raw=match.group("created"),
                document_number=match.group("doc"),
                bin_iin=match.group("bin"),
                applicant_name=applicant,
                document_type=doc_type,
                status=status,
                source_url=source_url,
            )
        )
    return records


def _find_status_at_end(text: str) -> str:
    t = norm(text)
    for status in sorted(KNOWN_STATUSES, key=len, reverse=True):
        if t.endswith(norm(status)):
            return status
    return ""


def _find_doc_type(text: str) -> str:
    t = norm(text)
    for doc_type in sorted(KNOWN_DOC_TYPES, key=len, reverse=True):
        if norm(doc_type) in t:
            return doc_type
    return ""


def filter_records(
    records: Iterable[ApplicationRecord],
    doc_type: str = DEFAULT_DOC_TYPE,
    statuses: Sequence[str] = DEFAULT_STATUSES,
) -> List[ApplicationRecord]:
    doc_type_n = norm(doc_type)
    statuses_n = {norm(s) for s in statuses}
    filtered = [r for r in records if norm(r.document_type) == doc_type_n and norm(r.status) in statuses_n]
    filtered.sort(key=lambda r: r.created_at or r.created_at_raw, reverse=True)
    return filtered


def scrape_applications(pages: int = 5, delay_seconds: float = 0.4) -> List[ApplicationRecord]:
    session = build_session()
    all_records: List[ApplicationRecord] = []
    for page in range(1, pages + 1):
        url = page_url(page)
        html = fetch_page(session, page)
        all_records.extend(parse_html_page(html, url))
        if delay_seconds and page < pages:
            time.sleep(delay_seconds)
    # Убираем дубли, если страницы сдвинулись во время обхода.
    dedup = {}
    for item in all_records:
        dedup[item.key] = item
    return list(dedup.values())
