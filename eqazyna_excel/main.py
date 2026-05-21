from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from .exporter import export_to_excel
from .pipeline import collect_records, enrich_records
from .scraper import TARGET_DOC_TYPE, TARGET_STATUSES
from .settings import PROJECT_ROOT, load_settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Выгрузка заявок e-Qazyna в Excel с обогащением по БИН через data.egov.kz",
    )
    parser.add_argument("--pages", type=int, default=5, help="Сколько страниц реестра e-Qazyna читать. По умолчанию 5.")
    parser.add_argument("--doc-type", default=TARGET_DOC_TYPE, help="Тип документа для фильтрации.")
    parser.add_argument(
        "--statuses",
        default=",".join(TARGET_STATUSES),
        help="Статусы через запятую. По умолчанию: Отправлено на рассмотрение,Принято",
    )
    parser.add_argument("--no-egov", action="store_true", help="Не обращаться к data.egov.kz, выгрузить только e-Qazyna + поисковые ссылки.")
    parser.add_argument("--env", default=None, help="Путь к .env, если он не в корне проекта.")
    parser.add_argument("--regions", default=str(PROJECT_ROOT / "config" / "regions.yaml"), help="Путь к config/regions.yaml")
    parser.add_argument("--output", default=None, help="Путь к итоговому xlsx. Если не указан, создаётся exports/eqazyna_YYYYMMDD_HHMMSS.xlsx")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = load_settings(args.env)
    statuses = [s.strip() for s in args.statuses.split(",") if s.strip()]

    print(f"Читаю e-Qazyna: страниц={args.pages}, тип='{args.doc_type}', статусы={statuses}")
    records = collect_records(settings, pages=args.pages, document_type=args.doc_type, statuses=statuses)
    print(f"Найдено подходящих заявок: {len(records)}")

    if not records:
        print("Подходящих заявок нет. Excel всё равно будет создан с заголовками.")

    if not args.no_egov and not settings.egov_api_key:
        print("ВНИМАНИЕ: EGOV_API_KEY не задан. Обогащение по БИН будет с ошибкой в колонке eGov.")

    print("Обогащаю по БИН и собираю поисковые ссылки...")
    rows = enrich_records(records, settings, regions_path=args.regions, use_egov=not args.no_egov)

    if args.output:
        output = Path(args.output)
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = settings.export_dir / f"eqazyna_applications_{ts}.xlsx"

    export_to_excel(rows, output)
    print(f"Готово: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
