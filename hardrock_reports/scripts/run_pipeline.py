#!/usr/bin/env python3
"""Main entry point for the Hardrock 100 extraction pipeline.

Usage:
    python scripts/run_pipeline.py --input input/hardrock_100_race_reports_urls.csv --out hardrock_reports

Optional flags:
    --limit 10          Process only the first N pending URLs
    --report-id HR_2025_001   Process a single report
    --refetch           Re-download even if raw HTML exists
    --skip-images       Skip the image download stage
    --skip-render       Skip rendering fallback for thin pages
    --resume            (default behavior) Skip already-completed work
    --verbose           Enable debug logging
"""

import argparse
import logging
import sys
import time
from pathlib import Path

# Ensure the project root is on sys.path so "scripts." imports work
# when invoked as: python scripts/run_pipeline.py
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.utils import setup_logging

logger = logging.getLogger("hardrock.pipeline")


def main():
    parser = argparse.ArgumentParser(
        description="Hardrock 100 Race Report Extraction Pipeline",
    )
    parser.add_argument(
        "--input", required=True,
        help="Path to the input CSV (e.g. input/hardrock_100_race_reports_urls.csv)",
    )
    parser.add_argument(
        "--out", default="hardrock_reports",
        help="Base output directory (default: hardrock_reports)",
    )
    parser.add_argument("--limit", type=int, default=None, help="Limit to N URLs")
    parser.add_argument("--report-id", default=None, help="Process a single report ID")
    parser.add_argument("--refetch", action="store_true", help="Re-fetch already-downloaded pages")
    parser.add_argument("--skip-images", action="store_true", help="Skip image extraction")
    parser.add_argument("--skip-render", action="store_true", help="Skip rendering fallback")
    parser.add_argument("--resume", action="store_true", help="Resume (default behavior)")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    setup_logging(args.verbose)
    start_time = time.monotonic()

    input_csv = Path(args.input)
    base_dir = Path(args.out)

    if not input_csv.exists():
        logger.error("Input CSV not found: %s", input_csv)
        sys.exit(1)

    # -----------------------------------------------------------------------
    # Stage 1: Normalize input
    # -----------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("STAGE 1: Normalize input")
    logger.info("=" * 60)

    from scripts.normalize_input import run as normalize_run
    records, norm_failures = normalize_run(input_csv, base_dir)

    if not records:
        logger.error("No valid records after normalization – exiting")
        sys.exit(1)

    # -----------------------------------------------------------------------
    # Stage 2 & 3: Fetch pages (with optional rendering fallback)
    # -----------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("STAGE 2/3: Fetch pages")
    logger.info("=" * 60)

    from scripts.fetch_pages import run as fetch_run
    records = fetch_run(
        records,
        base_dir,
        skip_render=args.skip_render,
        refetch=args.refetch,
        limit=args.limit,
        report_id_filter=args.report_id,
    )

    # -----------------------------------------------------------------------
    # Stage 4: Extract articles
    # -----------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("STAGE 4: Extract articles")
    logger.info("=" * 60)

    from scripts.extract_articles import run as extract_run
    records = extract_run(
        records,
        base_dir,
        limit=args.limit,
        report_id_filter=args.report_id,
    )

    # -----------------------------------------------------------------------
    # Stage 5: Extract and download images
    # -----------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("STAGE 5: Extract images")
    logger.info("=" * 60)

    from scripts.extract_images import run as images_run
    records, all_images = images_run(
        records,
        base_dir,
        skip_images=args.skip_images,
        limit=args.limit,
        report_id_filter=args.report_id,
    )

    # -----------------------------------------------------------------------
    # Stage 6: Build manifests
    # -----------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("STAGE 6: Build manifests")
    logger.info("=" * 60)

    from scripts.build_manifests import run as manifests_run
    manifests_run(records, all_images, base_dir)

    # -----------------------------------------------------------------------
    # QC checks and summary
    # -----------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info("QC CHECKS")
    logger.info("=" * 60)

    from scripts.qc_checks import run as qc_run
    qc_run(records, all_images, base_dir)

    elapsed = round(time.monotonic() - start_time, 1)
    logger.info("Pipeline completed in %.1f seconds", elapsed)


if __name__ == "__main__":
    main()
