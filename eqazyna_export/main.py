from __future__ import annotations

import argparse
import os
from pathlib import Path

from .pipeline import run_export
from .scraper import DEFAULT_DOC_TYPE, DEFAULT_STATUSES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export filtered e-Qazyna registry rows to XLSX with BIN enrichment.")
    parser.add_argument("--pages", type=int, default=int(os.getenv("EQAZYNA_PAGES", "5")), help="How many newest registry pages to read")
    parser.add_argument("--out", default="exports/eqazyna_export.xlsx", help="Output XLSX path")
    parser.add_argument("--doc-type", default=DEFAULT_DOC_TYPE, help="Document type filter")
    parser.add_argument(
        "--statuses",
        default=",".join(DEFAULT_STATUSES),
        help="Comma-separated statuses, e.g. 'Отправлено на рассмотрение,Принято'",
    )
    parser.add_argument("--no-egov", action="store_true", help="Do not call data.egov.kz")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    statuses = [x.strip() for x in args.statuses.split(",") if x.strip()]
    output = run_export(
        pages=max(1, args.pages),
        output_path=Path(args.out),
        doc_type=args.doc_type,
        statuses=statuses,
        use_egov=not args.no_egov,
    )
    print(f"Excel export created: {output}")


if __name__ == "__main__":
    main()
