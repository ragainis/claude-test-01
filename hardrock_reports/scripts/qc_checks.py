"""Quality checks and run summary for the extraction pipeline."""

import csv
import logging
from pathlib import Path

from scripts.utils import manifests_dir

logger = logging.getLogger("hardrock.qc")


def run_qc(records: list[dict], all_images: list[dict], base_dir: Path) -> dict:
    """Run quality checks on the extraction results.

    Returns a summary dict with counts and flagged issues.
    """
    issues = []
    stats = {
        "total_urls": len(records),
        "fetched": 0,
        "extracted": 0,
        "partial": 0,
        "failed": 0,
        "pending": 0,
        "total_images": len(all_images),
        "images_downloaded": 0,
        "images_failed": 0,
        "issues": [],
    }

    for r in records:
        status = r.get("status", "pending")
        if status == "fetched":
            stats["fetched"] += 1
        elif status == "extracted":
            stats["extracted"] += 1
        elif status == "partial":
            stats["partial"] += 1
        elif status == "failed":
            stats["failed"] += 1
        else:
            stats["pending"] += 1

        report_id = r.get("report_id", "???")

        # QC: low word count
        try:
            wc = int(r.get("word_count", 0) or 0)
        except (ValueError, TypeError):
            wc = 0

        if status in ("extracted", "partial") and wc < 250:
            issues.append(f"{report_id}: word_count={wc} (below 250 threshold)")

        # QC: zero extracted text
        if status == "extracted" and wc == 0:
            issues.append(f"{report_id}: zero extracted text")

        # QC: missing raw HTML
        raw_path = r.get("raw_html_path", "")
        if status in ("fetched", "extracted") and not raw_path:
            issues.append(f"{report_id}: missing raw_html_path")

        # QC: missing title
        article_title = r.get("article_title", "")
        title_seed = r.get("title_seed", "")
        if status == "extracted" and not article_title and not title_seed:
            issues.append(f"{report_id}: no article title and no seed title")

        # QC: low extraction confidence
        try:
            confidence = float(r.get("extraction_confidence", 0) or 0)
        except (ValueError, TypeError):
            confidence = 0
        if status == "extracted" and confidence < 0.3:
            issues.append(
                f"{report_id}: extraction_confidence={confidence:.2f} (below 0.3)"
            )

        # QC: zero images on an extracted report
        try:
            num_images = int(r.get("num_images", 0) or 0)
        except (ValueError, TypeError):
            num_images = 0
        if status == "extracted" and num_images == 0:
            issues.append(f"{report_id}: zero images extracted")

    # Image stats
    for img in all_images:
        if img.get("download_status") == "success":
            stats["images_downloaded"] += 1
        else:
            stats["images_failed"] += 1

    stats["issues"] = issues
    return stats


def print_summary(stats: dict) -> None:
    """Print a human-readable run summary."""
    print("\n" + "=" * 60)
    print("  HARDROCK EXTRACTION PIPELINE – RUN SUMMARY")
    print("=" * 60)
    print(f"  Total URLs:             {stats['total_urls']}")
    print(f"  Fetched successfully:   {stats['fetched']}")
    print(f"  Extracted successfully: {stats['extracted']}")
    print(f"  Partial:                {stats['partial']}")
    print(f"  Failed:                 {stats['failed']}")
    print(f"  Pending:                {stats['pending']}")
    print(f"  Total images found:     {stats['total_images']}")
    print(f"  Images downloaded:      {stats['images_downloaded']}")
    print(f"  Images failed:          {stats['images_failed']}")

    issues = stats.get("issues", [])
    if issues:
        print(f"\n  QC Issues ({len(issues)}):")
        for issue in issues:
            print(f"    ⚠ {issue}")
    else:
        print("\n  No QC issues found.")

    print("=" * 60 + "\n")


def run(records: list[dict], all_images: list[dict], base_dir: Path) -> dict:
    """Run QC checks and print summary."""
    stats = run_qc(records, all_images, base_dir)
    print_summary(stats)
    return stats
