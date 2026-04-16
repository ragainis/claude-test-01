"""Stage 5: Extract and download images from fetched pages."""

import argparse
import logging
import mimetypes
import os
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from scripts.utils import (
    FAILED_URLS_COLUMNS,
    IMAGES_COLUMNS,
    append_csv_row,
    ensure_dir,
    images_dir,
    looks_decorative,
    make_image_id,
    manifests_dir,
    processed_dir,
    raw_dir,
    read_json,
    sha256_bytes,
    sha256_file,
    write_json,
)

logger = logging.getLogger("hardrock.extract_images")

USER_AGENT = (
    "HardrockCorpusBot/1.0 "
    "(research extraction; +https://github.com/ragainis/claude-test-01)"
)
DOWNLOAD_TIMEOUT = 20
RATE_LIMIT_DELAY = 0.5
MAX_IMAGES_PER_REPORT = 50


def _get_image_dimensions(path: Path) -> tuple[int, int]:
    """Get image width and height using Pillow."""
    try:
        from PIL import Image
        with Image.open(path) as img:
            return img.size  # (width, height)
    except Exception:
        return (0, 0)


def _guess_extension(url: str, content_type: str = "") -> str:
    """Guess file extension from URL or content type."""
    # From content type
    if content_type:
        ext = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if ext:
            return ext

    # From URL path
    parsed = urlparse(url)
    path = parsed.path.lower()
    for ext in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".tiff"):
        if path.endswith(ext):
            return ext

    return ".jpg"  # default


def _get_context_text(tag, max_chars: int = 200) -> str:
    """Get a snippet of surrounding text near an image."""
    # Try parent paragraph or figure
    for parent in tag.parents:
        if parent.name in ("p", "figure", "figcaption", "div"):
            text = parent.get_text(strip=True)
            if text and len(text) > 10:
                return text[:max_chars]
    # Try next/prev sibling
    for sibling in [tag.next_sibling, tag.previous_sibling]:
        if sibling and hasattr(sibling, "get_text"):
            text = sibling.get_text(strip=True)
            if text and len(text) > 10:
                return text[:max_chars]
    return ""


def _get_caption(tag) -> str:
    """Try to find a caption for an image."""
    # Check for <figcaption> in parent <figure>
    figure = tag.find_parent("figure")
    if figure:
        figcap = figure.find("figcaption")
        if figcap:
            return figcap.get_text(strip=True)

    # Check for a nearby caption-like element
    next_elem = tag.find_next_sibling()
    if next_elem and next_elem.name in ("p", "span", "div"):
        cls = " ".join(next_elem.get("class", []))
        if "caption" in cls.lower() or "wp-caption" in cls.lower():
            return next_elem.get_text(strip=True)

    return ""


def find_content_images(html: str, page_url: str) -> list[dict]:
    """Find meaningful images in the HTML.

    Returns list of dicts with: image_url, alt_text, caption, context_text, is_decorative.
    """
    soup = BeautifulSoup(html, "lxml")

    # Try to scope to article content first
    content_root = None
    for selector in ["article", "main", "[role=main]",
                     ".post-content", ".entry-content", ".article-body"]:
        content_root = soup.select_one(selector)
        if content_root:
            break

    if content_root is None:
        content_root = soup.find("body") or soup

    images = []
    seen_urls = set()

    for img in content_root.find_all("img", src=True):
        src = img.get("src", "").strip()
        if not src:
            continue

        # Resolve relative URLs
        abs_url = urljoin(page_url, src)

        # Also check srcset for higher-res version
        srcset = img.get("srcset", "")
        if srcset:
            # Take the largest from srcset
            parts = [p.strip().split() for p in srcset.split(",") if p.strip()]
            for part in parts:
                if part:
                    candidate = urljoin(page_url, part[0])
                    if candidate not in seen_urls:
                        abs_url = candidate  # prefer last/largest

        if abs_url in seen_urls:
            continue
        seen_urls.add(abs_url)

        alt = img.get("alt", "").strip()
        width = 0
        height = 0
        try:
            width = int(img.get("width", 0))
            height = int(img.get("height", 0))
        except (ValueError, TypeError):
            pass

        is_dec = looks_decorative(abs_url, alt, width, height)
        caption = _get_caption(img)
        context = _get_context_text(img)

        images.append({
            "image_url": abs_url,
            "alt_text": alt,
            "caption": caption,
            "context_text": context,
            "is_decorative": is_dec,
            "width_hint": width,
            "height_hint": height,
        })

    return images


def download_images(
    record: dict,
    base_dir: Path,
    image_candidates: list[dict],
    *,
    skip_decorative: bool = True,
) -> list[dict]:
    """Download images for a report. Returns list of image metadata dicts."""
    report_id = record["report_id"]
    img_dir = images_dir(base_dir, report_id)
    pdir = processed_dir(base_dir, report_id)
    page_url = record.get("final_url") or record.get("normalized_url", "")
    failed_path = manifests_dir(base_dir) / "failed_urls.csv"

    downloaded = []
    seq = 0
    seen_hashes = set()

    for candidate in image_candidates[:MAX_IMAGES_PER_REPORT]:
        if skip_decorative and candidate.get("is_decorative"):
            logger.debug("%s: skipping decorative image %s", report_id, candidate["image_url"][:60])
            continue

        image_url = candidate["image_url"]
        seq += 1
        image_id = make_image_id(report_id, seq)

        try:
            with httpx.Client(
                follow_redirects=True,
                timeout=DOWNLOAD_TIMEOUT,
                headers={"User-Agent": USER_AGENT},
            ) as client:
                resp = client.get(image_url)
                resp.raise_for_status()

            content_type = resp.headers.get("content-type", "")
            ext = _guess_extension(image_url, content_type)
            filename = f"IMG_{seq:03d}{ext}"
            local_path = img_dir / filename

            data = resp.content
            file_hash = sha256_bytes(data)

            # Check for duplicate
            is_dup = file_hash in seen_hashes
            seen_hashes.add(file_hash)

            if is_dup:
                logger.debug("%s: duplicate image %s – still saving", report_id, image_url[:60])

            local_path.write_bytes(data)

            # Get actual dimensions
            width, height = _get_image_dimensions(local_path)

            # Mime type
            mime = content_type.split(";")[0].strip() if content_type else ""
            if not mime:
                mime = mimetypes.guess_type(str(local_path))[0] or ""

            downloaded.append({
                "report_id": report_id,
                "image_id": image_id,
                "page_url": page_url,
                "image_url": image_url,
                "local_path": str(local_path.relative_to(base_dir)),
                "mime_type": mime,
                "width": width,
                "height": height,
                "sha256": file_hash,
                "phash": "",
                "alt_text": candidate.get("alt_text", ""),
                "caption": candidate.get("caption", ""),
                "context_text": candidate.get("context_text", ""),
                "is_decorative": candidate.get("is_decorative", False),
                "is_duplicate": is_dup,
                "download_status": "success",
                "notes": "",
            })

            logger.debug("%s: downloaded %s -> %s", report_id, image_url[:60], filename)
            time.sleep(RATE_LIMIT_DELAY)

        except Exception as exc:
            logger.warning(
                "%s: failed to download %s – %s", report_id, image_url[:60], exc
            )
            downloaded.append({
                "report_id": report_id,
                "image_id": image_id,
                "page_url": page_url,
                "image_url": image_url,
                "local_path": "",
                "mime_type": "",
                "width": 0,
                "height": 0,
                "sha256": "",
                "phash": "",
                "alt_text": candidate.get("alt_text", ""),
                "caption": candidate.get("caption", ""),
                "context_text": candidate.get("context_text", ""),
                "is_decorative": candidate.get("is_decorative", False),
                "is_duplicate": False,
                "download_status": "failed",
                "notes": str(exc)[:200],
            })

    return downloaded


def extract_images_for_one(record: dict, base_dir: Path, all_images: list[dict]) -> dict:
    """Extract and download images for a single report. Mutates record."""
    report_id = record["report_id"]
    rdir = raw_dir(base_dir, report_id)
    pdir = processed_dir(base_dir, report_id)

    # Check for existing image_metadata.csv (resume support)
    meta_path = pdir / "image_metadata.csv"
    if meta_path.exists() and meta_path.stat().st_size > 0:
        logger.info("%s: images already extracted – skipping", report_id)
        return record

    # Determine HTML source
    rendered_path = rdir / "rendered.html"
    source_path = rdir / "source.html"
    if rendered_path.exists() and rendered_path.stat().st_size > 0:
        html = rendered_path.read_text(encoding="utf-8", errors="replace")
    elif source_path.exists() and source_path.stat().st_size > 0:
        html = source_path.read_text(encoding="utf-8", errors="replace")
    else:
        logger.warning("%s: no HTML for image extraction", report_id)
        return record

    page_url = record.get("final_url") or record.get("normalized_url", "")

    # Find candidate images
    candidates = find_content_images(html, page_url)
    logger.info("%s: found %d candidate images", report_id, len(candidates))

    if not candidates:
        # Write empty metadata file
        from scripts.utils import write_csv
        write_csv(meta_path, [], IMAGES_COLUMNS)
        record["num_images"] = 0
        return record

    # Download
    image_records = download_images(record, base_dir, candidates)
    successful = [r for r in image_records if r["download_status"] == "success"]

    # Write per-report image_metadata.csv
    from scripts.utils import write_csv
    write_csv(meta_path, image_records, IMAGES_COLUMNS)

    # Update article.json with image references
    article_json_path = pdir / "article.json"
    if article_json_path.exists():
        try:
            article_data = read_json(article_json_path)
            article_data["images"] = [
                {
                    "image_id": r["image_id"],
                    "image_url": r["image_url"],
                    "local_path": r["local_path"],
                    "alt_text": r["alt_text"],
                    "caption": r["caption"],
                    "context_text": r["context_text"],
                }
                for r in successful
            ]
            write_json(article_json_path, article_data)
        except Exception as exc:
            logger.warning("%s: could not update article.json – %s", report_id, exc)

    record["num_images"] = len(successful)
    all_images.extend(image_records)

    logger.info(
        "%s: downloaded %d/%d images",
        report_id, len(successful), len(candidates),
    )
    return record


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run(
    records: list[dict],
    base_dir: Path,
    *,
    skip_images: bool = False,
    limit: int | None = None,
    report_id_filter: str | None = None,
) -> tuple[list[dict], list[dict]]:
    """Extract images for all extracted records.

    Returns (records, all_image_records).
    """
    if skip_images:
        logger.info("Skipping image extraction (--skip-images)")
        return records, []

    targets = [r for r in records if r["status"] in ("extracted", "partial")]
    if report_id_filter:
        targets = [r for r in targets if r["report_id"] == report_id_filter]
    if limit:
        targets = targets[:limit]

    all_images: list[dict] = []

    for i, record in enumerate(targets, 1):
        logger.info("Extracting images %d/%d: %s", i, len(targets), record["report_id"])
        try:
            extract_images_for_one(record, base_dir, all_images)
        except Exception as exc:
            logger.error("%s: image extraction error – %s", record["report_id"], exc)
            record["notes"] = (
                (record.get("notes", "") + "; " if record.get("notes") else "")
                + f"Image extraction error: {exc}"
            )

    total = len(all_images)
    ok = sum(1 for r in all_images if r["download_status"] == "success")
    logger.info("Image extraction complete: %d downloaded, %d total candidates", ok, total)
    return records, all_images


def main():
    parser = argparse.ArgumentParser(description="Stage 5: Extract and download images")
    parser.add_argument("--input", required=True, help="Path to input CSV")
    parser.add_argument("--out", default="hardrock_reports", help="Base output directory")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    from scripts.normalize_input import run as normalize_run
    from scripts.utils import setup_logging

    setup_logging(args.verbose)
    records, _ = normalize_run(Path(args.input), Path(args.out))
    # Mark extracted ones
    for r in records:
        pdir = processed_dir(Path(args.out), r["report_id"])
        if (pdir / "article.json").exists():
            r["status"] = "extracted"
    run(records, Path(args.out), limit=args.limit)


if __name__ == "__main__":
    main()
