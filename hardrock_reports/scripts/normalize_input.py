"""Stage 1: Normalize input CSV – validate, clean, assign report IDs."""

import argparse
import csv
import logging
import sys
from collections import defaultdict
from pathlib import Path

from scripts.utils import (
    FAILED_URLS_COLUMNS,
    REPORTS_COLUMNS,
    append_csv_row,
    extract_domain,
    is_valid_url,
    make_report_id,
    normalize_url,
    setup_logging,
    utc_now_iso,
)

logger = logging.getLogger("hardrock.normalize")

REQUIRED_INPUT_COLUMNS = {"year", "title", "url", "source_page"}


def read_input_csv(path: Path) -> list[dict]:
    """Read the input CSV and return rows as dicts."""
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not REQUIRED_INPUT_COLUMNS.issubset(set(reader.fieldnames or [])):
            missing = REQUIRED_INPUT_COLUMNS - set(reader.fieldnames or [])
            raise ValueError(f"Input CSV missing required columns: {missing}")
        return list(reader)


def normalize_rows(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Normalize rows and assign stable report IDs.

    Returns (records, failures) where records follow the reports schema
    and failures follow the failed_urls schema.
    """
    # Group by year to assign sequential IDs within each year
    year_counters: dict[int, int] = defaultdict(int)
    records = []
    failures = []

    # Sort by year then by original order for deterministic ID assignment
    for row in rows:
        raw_year = str(row.get("year", "")).strip()
        raw_url = str(row.get("url", "")).strip()
        raw_title = str(row.get("title", "")).strip()
        raw_source_page = str(row.get("source_page", "")).strip()

        # Validate year
        try:
            year = int(raw_year)
        except (ValueError, TypeError):
            logger.warning("Invalid year %r for URL %r – skipping", raw_year, raw_url)
            failures.append({
                "report_id": "",
                "url": raw_url,
                "final_url": "",
                "failure_stage": "normalize",
                "error_type": "invalid_year",
                "error_message": f"Cannot parse year: {raw_year!r}",
                "retry_recommended": "false",
            })
            continue

        # Assign ID
        year_counters[year] += 1
        report_id = make_report_id(year, year_counters[year])

        # Normalize URL
        normalized = normalize_url(raw_url)
        if not is_valid_url(normalized):
            logger.warning("%s: malformed URL %r – logging failure", report_id, raw_url)
            failures.append({
                "report_id": report_id,
                "url": raw_url,
                "final_url": "",
                "failure_stage": "normalize",
                "error_type": "invalid_url",
                "error_message": f"URL failed validation after normalization: {raw_url!r}",
                "retry_recommended": "false",
            })
            # Still create a record so it shows up in reports.csv
            records.append(_make_record(
                report_id, year, raw_title, raw_url, raw_source_page,
                normalized, status="failed",
                notes="Malformed URL – failed normalization",
            ))
            continue

        domain = extract_domain(normalized)
        records.append(_make_record(
            report_id, year, raw_title, raw_url, raw_source_page,
            normalized, domain=domain,
        ))

    logger.info(
        "Normalized %d records (%d failures) from %d input rows",
        len(records), len(failures), len(rows),
    )
    return records, failures


def _make_record(
    report_id: str,
    year: int,
    title_seed: str,
    source_url: str,
    source_page: str,
    normalized_url: str,
    domain: str = "",
    status: str = "pending",
    notes: str = "",
) -> dict:
    return {
        "report_id": report_id,
        "year": year,
        "title_seed": title_seed,
        "source_url": source_url,
        "source_page": source_page,
        "normalized_url": normalized_url,
        "final_url": "",
        "domain": domain,
        "status": status,
        "fetch_status_code": "",
        "fetch_timestamp_utc": "",
        "used_rendering": "",
        "article_title": "",
        "author": "",
        "published_date": "",
        "language": "",
        "word_count": "",
        "num_images": "",
        "extraction_method": "",
        "extraction_confidence": "",
        "raw_html_path": "",
        "article_json_path": "",
        "article_txt_path": "",
        "chunks_path": "",
        "notes": notes,
    }


def run(input_csv: Path, base_dir: Path) -> tuple[list[dict], list[dict]]:
    """Run the normalization stage. Returns (records, failures)."""
    logger.info("Reading input CSV: %s", input_csv)
    rows = read_input_csv(input_csv)
    records, failures = normalize_rows(rows)

    # Write failures immediately
    if failures:
        from scripts.utils import manifests_dir, write_csv
        failed_path = manifests_dir(base_dir) / "failed_urls.csv"
        write_csv(failed_path, failures, FAILED_URLS_COLUMNS)
        logger.info("Wrote %d normalization failures to %s", len(failures), failed_path)

    return records, failures


def main():
    parser = argparse.ArgumentParser(description="Stage 1: Normalize input CSV")
    parser.add_argument("--input", required=True, help="Path to input CSV")
    parser.add_argument("--out", default="hardrock_reports", help="Base output directory")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    setup_logging(args.verbose)
    records, failures = run(Path(args.input), Path(args.out))

    print(f"\nNormalized: {len(records)} records, {len(failures)} failures")
    for r in records[:5]:
        print(f"  {r['report_id']}: {r['normalized_url'][:80]}")
    if len(records) > 5:
        print(f"  ... and {len(records) - 5} more")


if __name__ == "__main__":
    main()
