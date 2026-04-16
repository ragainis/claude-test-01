"""Stage 6: Build corpus-level manifests from per-report data."""

import argparse
import csv
import logging
from pathlib import Path

from scripts.utils import (
    CRAWL_LOG_COLUMNS,
    FAILED_URLS_COLUMNS,
    IMAGES_COLUMNS,
    REPORTS_COLUMNS,
    ensure_dir,
    manifests_dir,
    write_csv,
)

logger = logging.getLogger("hardrock.manifests")


def build_reports_csv(records: list[dict], base_dir: Path) -> Path:
    """Write the master reports.csv manifest."""
    path = manifests_dir(base_dir) / "reports.csv"
    write_csv(path, records, REPORTS_COLUMNS)
    logger.info("Wrote %d rows to %s", len(records), path)
    return path


def build_images_csv(all_images: list[dict], base_dir: Path) -> Path:
    """Write the master images.csv manifest."""
    path = manifests_dir(base_dir) / "images.csv"
    write_csv(path, all_images, IMAGES_COLUMNS)
    logger.info("Wrote %d rows to %s", len(all_images), path)
    return path


def consolidate_crawl_log(base_dir: Path) -> Path:
    """The crawl_log.csv is written incrementally during fetch.

    This function ensures it exists and returns its path.
    """
    path = manifests_dir(base_dir) / "crawl_log.csv"
    if not path.exists():
        write_csv(path, [], CRAWL_LOG_COLUMNS)
        logger.info("Created empty crawl_log.csv")
    else:
        # Count rows
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = sum(1 for _ in reader) - 1  # minus header
        logger.info("crawl_log.csv has %d entries", rows)
    return path


def consolidate_failed_urls(records: list[dict], base_dir: Path) -> Path:
    """Rebuild failed_urls.csv from current state + any existing entries.

    Merges incremental failures written during fetch/extract with
    any records that ended up in a failed state.
    """
    path = manifests_dir(base_dir) / "failed_urls.csv"

    # Read existing failures (written incrementally)
    existing = {}
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = (row.get("report_id", ""), row.get("failure_stage", ""))
                existing[key] = row

    # Add any records in failed state that don't already have an entry
    for r in records:
        if r["status"] == "failed":
            key = (r["report_id"], "")
            # Check if any entry exists for this report_id
            has_entry = any(k[0] == r["report_id"] for k in existing)
            if not has_entry:
                existing[key] = {
                    "report_id": r["report_id"],
                    "url": r.get("normalized_url", r.get("source_url", "")),
                    "final_url": r.get("final_url", ""),
                    "failure_stage": "fetch",
                    "error_type": "unknown",
                    "error_message": r.get("notes", ""),
                    "retry_recommended": "false",
                }

    rows = list(existing.values())
    write_csv(path, rows, FAILED_URLS_COLUMNS)
    logger.info("Wrote %d rows to %s", len(rows), path)
    return path


def run(
    records: list[dict],
    all_images: list[dict],
    base_dir: Path,
) -> dict[str, Path]:
    """Build all manifests. Returns dict of manifest name -> path."""
    logger.info("Building manifests...")

    paths = {
        "reports": build_reports_csv(records, base_dir),
        "images": build_images_csv(all_images, base_dir),
        "crawl_log": consolidate_crawl_log(base_dir),
        "failed_urls": consolidate_failed_urls(records, base_dir),
    }

    logger.info("All manifests written to %s", manifests_dir(base_dir))
    return paths


def main():
    parser = argparse.ArgumentParser(description="Stage 6: Build manifests")
    parser.add_argument("--out", default="hardrock_reports", help="Base output directory")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    from scripts.utils import setup_logging
    setup_logging(args.verbose)

    # This standalone mode rebuilds from whatever is on disk
    logger.info("Rebuilding manifests from disk (standalone mode)")
    # Minimal implementation – the full pipeline passes records directly
    run([], [], Path(args.out))


if __name__ == "__main__":
    main()
