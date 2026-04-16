"""Shared constants, schemas, and helpers for the Hardrock extraction pipeline."""

import csv
import hashlib
import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, urlunparse

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def setup_logging(verbose: bool = False) -> logging.Logger:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format=LOG_FORMAT)
    return logging.getLogger("hardrock")


# ---------------------------------------------------------------------------
# ID generation
# ---------------------------------------------------------------------------


def make_report_id(year: int, sequence: int) -> str:
    return f"HR_{year}_{sequence:03d}"


def make_image_id(report_id: str, sequence: int) -> str:
    return f"{report_id}_IMG_{sequence:03d}"


def make_chunk_id(report_id: str, sequence: int) -> str:
    return f"{report_id}_CH_{sequence:03d}"


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------


def normalize_url(url: str) -> str:
    """Normalize a URL: strip whitespace, standardize scheme, remove fragments."""
    url = url.strip()
    if not url:
        return ""
    # Add scheme if missing
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    parsed = urlparse(url)
    # Strip fragment unless it looks like a route (starts with /)
    fragment = ""
    if parsed.fragment and parsed.fragment.startswith("/"):
        fragment = parsed.fragment
    normalized = urlunparse((
        parsed.scheme,
        parsed.netloc.lower(),
        parsed.path.rstrip("/") if parsed.path != "/" else "/",
        parsed.params,
        parsed.query,
        fragment,
    ))
    return normalized


def extract_domain(url: str) -> str:
    """Extract the domain from a URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


def is_valid_url(url: str) -> bool:
    """Check if a URL is minimally valid."""
    try:
        parsed = urlparse(url)
        return bool(parsed.scheme) and bool(parsed.netloc)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# File / path helpers
# ---------------------------------------------------------------------------


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def raw_dir(base: Path, report_id: str) -> Path:
    return ensure_dir(base / "raw" / report_id)


def processed_dir(base: Path, report_id: str) -> Path:
    return ensure_dir(base / "processed" / report_id)


def images_dir(base: Path, report_id: str) -> Path:
    return ensure_dir(base / "processed" / report_id / "images")


def manifests_dir(base: Path) -> Path:
    return ensure_dir(base / "manifests")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# CSV / JSON helpers
# ---------------------------------------------------------------------------


def write_json(path: Path, data: dict, indent: int = 2) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def read_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def append_csv_row(path: Path, row: dict, fieldnames: list[str]) -> None:
    file_exists = path.exists() and path.stat().st_size > 0
    with open(path, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


# ---------------------------------------------------------------------------
# Schema column lists
# ---------------------------------------------------------------------------

REPORTS_COLUMNS = [
    "report_id", "year", "title_seed", "source_url", "source_page",
    "normalized_url", "final_url", "domain", "status",
    "fetch_status_code", "fetch_timestamp_utc", "used_rendering",
    "article_title", "author", "published_date", "language",
    "word_count", "num_images", "extraction_method", "extraction_confidence",
    "raw_html_path", "article_json_path", "article_txt_path",
    "chunks_path", "notes",
]

IMAGES_COLUMNS = [
    "report_id", "image_id", "page_url", "image_url", "local_path",
    "mime_type", "width", "height", "sha256", "phash",
    "alt_text", "caption", "context_text",
    "is_decorative", "is_duplicate", "download_status", "notes",
]

CRAWL_LOG_COLUMNS = [
    "report_id", "attempt", "timestamp_utc", "url", "method",
    "status_code", "used_rendering", "duration_seconds",
    "redirect_chain", "error_type", "error_message",
]

FAILED_URLS_COLUMNS = [
    "report_id", "url", "final_url", "failure_stage",
    "error_type", "error_message", "retry_recommended",
]

# ---------------------------------------------------------------------------
# Decorative image detection
# ---------------------------------------------------------------------------

DECORATIVE_PATTERNS = re.compile(
    r"(logo|icon|avatar|share|sprite|pixel|spacer|tracking|badge|widget|"
    r"button|banner-ad|ad-|advert|loading|spinner|emoji|favicon|gravatar)",
    re.IGNORECASE,
)

MIN_IMAGE_DIMENSION = 100  # pixels – skip tiny images


def looks_decorative(url: str, alt: str = "", width: int = 0, height: int = 0) -> bool:
    """Heuristic: does this image look decorative or non-content?"""
    if DECORATIVE_PATTERNS.search(url):
        return True
    if DECORATIVE_PATTERNS.search(alt):
        return True
    if width and height and (width < MIN_IMAGE_DIMENSION or height < MIN_IMAGE_DIMENSION):
        return True
    return False
