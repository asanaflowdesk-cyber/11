from __future__ import annotations

import re
from datetime import datetime
from typing import Iterable
from urllib.parse import urlencode

from bs4 import BeautifulSoup

from .models import ApplicationRecord
from .normalization import clean_text, digits_only, norm_key

TARGET_DOC_TYPE = "Заявка на разведку ТПИ"
TARGET_STATUSES = ("Отправлено на рассмотрение", "Принято")

KNOWN_DOC_TYPES = [
    "Оцифровка контракта",
    "Оцифровка лицензии ТПИ",
    "Переход на лицензионный режим",
    "Заявка на разведку ТПИ",
    "Миграция лицензии на разведку ТПИ",
    "Миграция лицензии на добычу ТПИ",
    "Миграция контракта на разведку ТПИ",
    "Миграция контракта на добычу ТПИ",
    "Миграция контракта на разведку и добычу ТПИ",
    "Миграция контракта на добычу ОПИ",
    "Заявка на продление лицензии на разведку ТПИ",
    "Заявка на добычу ТПИ",
    "Заявка на разведку и добычу",
    "Заявка на использование пространства недр",
    "Соглашение о переработке",
    "Регистрация договора залога ТПИ",
    "Оцифровка лицензии ОПИ",
    "Оцифровка контракта ОПИ",
    "Оцифровка контракта по подземным сооружениям",
    "Заявка на лицензию на добычу ОПИ",
    "Заявка на лицензию ОПИ",
    "Регистрация договора залога ОПИ",
    "Оцифровка лицензии Старательства",
    "Заявка на лицензию Старательства",
    "Заявка на использование ликвидационного фонда",
    "Согласование водоохранных мероприятий",
    "Горный/Геологический отвод",
    "Разрешение на застройку территорий залегания",
    "Разрешение на извелечение горной массы",
    "Переход права недропользования",
    "Преобразование участка недр",
    "Выдача лицензии на экспорт информации",
    "Выдача разрешения на временный вывоз в рамках ТС",
    "Геологическое изучение недр",
    "Заключение об отсутствии полезных ископаемых",
    "Заключение на строительство",
    "Отчетность ЛКУ",
    "Выдача заключения на строительство",
    "Системный документ",
    "Отрисовка участка по старательству",
    "Оцифровка месторождения",
    "Редактирование",
    "Внесение изменений в лицензию",
    "Приобретение геологической информации",
    "Изменения рабочего органа",
    "Внесение сведений по акту ликвидации/обследования",
    "Сдача акта ликвидации",
    "Прекращение действия лицензий",
    "Отзыв Лицензии",
    "Подписание Протоколов",
    "Гео отчетность",
]

KNOWN_STATUSES = [
    "Отправлено на рассмотрение",
    "Принято",
    "Выдана лицензия",
    "Отклонено",
    "Отозвано",
    "Аннулировано",
    "Завершено",
]

DATE_RE = re.compile(r"(?P<date>\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}:\d{2})")
ROW_START_RE = re.compile(
    r"^(?P<date>\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}:\d{2})\s+"
    r"(?P<doc>[0-9]+-[A-ZА-Я]+)\s+"
    r"(?P<bin>\d{12})\s+"
    r"(?P<rest>.+)$"
)


def build_page_url(base_url: str, page: int) -> str:
    if page <= 1:
        return base_url
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{urlencode({'p': page})}"


def parse_date(raw: str) -> datetime | None:
    raw = clean_text(raw)
    for fmt in ("%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def split_rest_into_name_type_status(rest: str) -> tuple[str, str, str] | None:
    rest = clean_text(rest)
    rest_norm = norm_key(rest)

    status_found: str | None = None
    status_pos = -1
    for status in KNOWN_STATUSES:
        pos = rest_norm.rfind(norm_key(status))
        if pos >= 0 and pos >= status_pos:
            status_found = status
            status_pos = pos
    if not status_found:
        return None

    before_status = clean_text(rest[:status_pos])
    before_norm = norm_key(before_status)

    doc_found: str | None = None
    doc_pos = -1
    # Longest match first so that "Заявка на продление..." is not cut as plain "Заявка...".
    for doc_type in sorted(KNOWN_DOC_TYPES, key=len, reverse=True):
        pos = before_norm.rfind(norm_key(doc_type))
        if pos >= 0 and pos >= doc_pos:
            doc_found = doc_type
            doc_pos = pos
    if not doc_found:
        return None

    applicant_name = clean_text(before_status[:doc_pos])
    return applicant_name, doc_found, status_found


def parse_row_values(values: list[str], source_url: str, source_page: int) -> ApplicationRecord | None:
    values = [clean_text(v) for v in values if clean_text(v)]
    if len(values) < 6:
        return None

    # Expected columns: date, document number, BIN, applicant, type, status.
    created_raw = values[0]
    document_number = values[1]
    applicant_bin = digits_only(values[2])
    applicant_name = values[3]
    document_type = values[4]
    status = values[5]

    if not applicant_bin or len(applicant_bin) != 12:
        return None
    if not DATE_RE.search(created_raw):
        return None

    return ApplicationRecord(
        created_at=parse_date(created_raw),
        created_at_raw=created_raw,
        document_number=document_number,
        applicant_bin=applicant_bin,
        applicant_name=applicant_name,
        document_type=document_type,
        status=status,
        source_url=source_url,
        source_page=source_page,
    )


def parse_text_line(line: str, source_url: str, source_page: int) -> ApplicationRecord | None:
    line = clean_text(line)
    match = ROW_START_RE.match(line)
    if not match:
        return None
    parsed = split_rest_into_name_type_status(match.group("rest"))
    if not parsed:
        return None
    applicant_name, document_type, status = parsed
    return ApplicationRecord(
        created_at=parse_date(match.group("date")),
        created_at_raw=match.group("date"),
        document_number=match.group("doc"),
        applicant_bin=digits_only(match.group("bin")),
        applicant_name=applicant_name,
        document_type=document_type,
        status=status,
        source_url=source_url,
        source_page=source_page,
    )


def parse_applications(html: str, source_url: str, source_page: int) -> list[ApplicationRecord]:
    soup = BeautifulSoup(html, "lxml")
    records: list[ApplicationRecord] = []

    # Primary path: real HTML tables.
    for table in soup.find_all("table"):
        table_text = norm_key(table.get_text(" ", strip=True))
        if "дата создания" not in table_text or "иин/бин" not in table_text:
            continue
        for tr in table.find_all("tr"):
            cells = [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
            row = parse_row_values(cells, source_url, source_page)
            if row:
                records.append(row)

    if records:
        return deduplicate(records)

    # Fallback: page rendered as text by server / stripped table markup.
    text = soup.get_text("\n", strip=True)
    for line in text.splitlines():
        row = parse_text_line(line, source_url, source_page)
        if row:
            records.append(row)
    return deduplicate(records)


def deduplicate(records: Iterable[ApplicationRecord]) -> list[ApplicationRecord]:
    seen: set[str] = set()
    result: list[ApplicationRecord] = []
    for record in records:
        key = record.unique_key
        if key in seen:
            continue
        seen.add(key)
        result.append(record)
    return result


def filter_applications(
    records: Iterable[ApplicationRecord],
    document_type: str = TARGET_DOC_TYPE,
    statuses: Iterable[str] = TARGET_STATUSES,
) -> list[ApplicationRecord]:
    doc_key = norm_key(document_type)
    status_keys = {norm_key(s) for s in statuses}
    result = []
    for rec in records:
        if norm_key(rec.document_type) != doc_key:
            continue
        if norm_key(rec.status) not in status_keys:
            continue
        result.append(rec)
    result.sort(key=lambda r: r.created_at or datetime.min, reverse=True)
    return result
