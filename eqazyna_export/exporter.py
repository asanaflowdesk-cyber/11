from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List

import xlsxwriter

from .models import ApplicationRecord, CompanyInfo
from .utils import make_search_links, safe_json

HEADERS = [
    "Дата создания",
    "Номер документа",
    "БИН/ИИН",
    "Заявитель из e-Qazyna",
    "Тип документа",
    "Статус заявки",
    "Наименование из eGov",
    "Юридический адрес eGov",
    "Регион по адресу",
    "Руководитель / контактное лицо из eGov",
    "Вид деятельности / ОКЭД",
    "Статус eGov",
    "Ошибка eGov",
    "Телефон (заполнить вручную)",
    "2GIS поиск",
    "Google поиск",
    "Яндекс поиск",
    "Источник e-Qazyna",
    "Raw eGov fields",
]


def write_excel(
    records: List[ApplicationRecord],
    companies: Dict[str, CompanyInfo],
    output_path: str | Path,
    generated_at: datetime | None = None,
) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    generated_at = generated_at or datetime.now()

    workbook = xlsxwriter.Workbook(str(output))
    workbook.set_properties(
        {
            "title": "e-Qazyna TPI exploration applications export",
            "subject": "Filtered e-Qazyna registry export with BIN enrichment",
            "author": "FlowDesk e-Qazyna exporter",
        }
    )

    header_fmt = workbook.add_format(
        {
            "bold": True,
            "font_color": "white",
            "bg_color": "#203040",
            "border": 1,
            "align": "center",
            "valign": "vcenter",
            "text_wrap": True,
        }
    )
    cell_fmt = workbook.add_format({"border": 1, "valign": "top", "text_wrap": True})
    date_fmt = workbook.add_format({"border": 1, "num_format": "dd.mm.yyyy hh:mm:ss", "valign": "top"})
    link_fmt = workbook.add_format({"border": 1, "font_color": "blue", "underline": 1, "valign": "top"})
    warning_fmt = workbook.add_format({"border": 1, "bg_color": "#FFF2CC", "valign": "top", "text_wrap": True})
    title_fmt = workbook.add_format({"bold": True, "font_size": 16, "font_color": "#203040"})
    kpi_fmt = workbook.add_format({"bold": True, "font_size": 14, "bg_color": "#EAF2F8", "border": 1, "align": "center"})

    sheet = workbook.add_worksheet("Заявки")
    sheet.freeze_panes(1, 0)
    sheet.autofilter(0, 0, max(len(records), 1), len(HEADERS) - 1)

    for col, header in enumerate(HEADERS):
        sheet.write(0, col, header, header_fmt)

    for row_idx, record in enumerate(records, start=1):
        company = companies.get(record.bin_iin, CompanyInfo(bin_iin=record.bin_iin, egov_status="not_requested"))
        address = company.legal_address
        links = make_search_links(record.bin_iin, company.egov_name or record.applicant_name, address)
        raw = safe_json(company.raw, limit=2500) if company.raw else ""

        values = [
            record.created_at or record.created_at_raw,
            record.document_number,
            record.bin_iin,
            record.applicant_name,
            record.document_type,
            record.status,
            company.egov_name,
            address,
            company.region,
            company.director,
            company.activity,
            company.egov_status,
            company.error,
            "",
            links["2gis"],
            links["google"],
            links["yandex"],
            record.source_url,
            raw,
        ]

        for col_idx, value in enumerate(values):
            fmt = date_fmt if col_idx == 0 and record.created_at else cell_fmt
            if col_idx in (12,) and value:
                fmt = warning_fmt
            if col_idx in (14, 15, 16, 17):
                sheet.write_url(row_idx, col_idx, value, link_fmt, "открыть")
            elif col_idx == 0 and record.created_at:
                sheet.write_datetime(row_idx, col_idx, record.created_at, fmt)
            else:
                sheet.write(row_idx, col_idx, value, fmt)

    widths = [20, 16, 16, 34, 28, 24, 34, 48, 24, 34, 36, 18, 28, 24, 14, 14, 14, 16, 60]
    for i, width in enumerate(widths):
        sheet.set_column(i, i, width)
    sheet.set_default_row(34)
    sheet.set_row(0, 42)

    # Сводка
    summary = workbook.add_worksheet("Сводка")
    summary.write("A1", "e-Qazyna выгрузка заявок", title_fmt)
    summary.write("A3", "Сформировано", header_fmt)
    summary.write("B3", generated_at.strftime("%d.%m.%Y %H:%M:%S"), cell_fmt)
    summary.write("A4", "Всего строк", header_fmt)
    summary.write("B4", len(records), kpi_fmt)
    summary.write("A5", "Уникальных БИН", header_fmt)
    summary.write("B5", len(set(r.bin_iin for r in records)), kpi_fmt)
    summary.write("A6", "Обогащено eGov", header_fmt)
    summary.write("B6", sum(1 for c in companies.values() if c.egov_found), kpi_fmt)

    status_counts: Dict[str, int] = {}
    region_counts: Dict[str, int] = {}
    for r in records:
        status_counts[r.status] = status_counts.get(r.status, 0) + 1
        c = companies.get(r.bin_iin)
        region = c.region if c and c.region else "Не определён"
        region_counts[region] = region_counts.get(region, 0) + 1

    summary.write("A8", "Статусы заявок", title_fmt)
    summary.write_row("A9", ["Статус", "Кол-во"], header_fmt)
    for i, (status, cnt) in enumerate(sorted(status_counts.items()), start=10):
        summary.write(i - 1, 0, status, cell_fmt)
        summary.write(i - 1, 1, cnt, cell_fmt)

    start_region = 9 + max(len(status_counts), 1) + 3
    summary.write(start_region - 1, 0, "Регионы по адресу компании", title_fmt)
    summary.write_row(start_region, 0, ["Регион", "Кол-во"], header_fmt)
    for offset, (region, cnt) in enumerate(sorted(region_counts.items(), key=lambda x: (-x[1], x[0])), start=1):
        summary.write(start_region + offset, 0, region, cell_fmt)
        summary.write(start_region + offset, 1, cnt, cell_fmt)

    summary.set_column("A:A", 36)
    summary.set_column("B:B", 18)

    # Инструкция
    instr = workbook.add_worksheet("Инструкция")
    instr.set_column("A:A", 120)
    lines = [
        "Как пользоваться файлом:",
        "1. Основной лист — 'Заявки'. Там уже стоят фильтры по шапке.",
        "2. Колонка 'Телефон' оставлена для ручного заполнения после проверки 2GIS/Google/Яндекс.",
        "3. Регион определяется по юридическому адресу из eGov. Это рабочая подсказка, а не гарантия фактического офиса.",
        "4. Если eGov не вернул данные, строка всё равно остаётся в файле: БИН и заявитель взяты из e-Qazyna.",
        "5. Ссылки поиска открываются кликом из Excel.",
        "6. Если адрес явно устарел — корректируйте вручную после проверки. Госданные тоже бывают как древний факс: формально есть, но доверять без проверки не стоит.",
    ]
    instr.write("A1", "Инструкция", title_fmt)
    for i, line in enumerate(lines, start=3):
        instr.write(i, 0, line, cell_fmt)

    workbook.close()
    return output
