"""Stage 4: Extract article text from fetched HTML pages."""

import argparse
import json
import logging
import re
from pathlib import Path

from bs4 import BeautifulSoup, Tag
from readability import Document

from scripts.utils import (
    FAILED_URLS_COLUMNS,
    append_csv_row,
    ensure_dir,
    manifests_dir,
    make_chunk_id,
    processed_dir,
    raw_dir,
    read_json,
    utc_now_iso,
    write_json,
)

logger = logging.getLogger("hardrock.extract_articles")


# ---------------------------------------------------------------------------
# Metadata extraction helpers
# ---------------------------------------------------------------------------


def _extract_meta(soup: BeautifulSoup, names: list[str]) -> str:
    """Extract content from meta tags by name or property."""
    for name in names:
        tag = soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return tag["content"].strip()
        tag = soup.find("meta", attrs={"property": name})
        if tag and tag.get("content"):
            return tag["content"].strip()
    return ""


def _extract_jsonld(soup: BeautifulSoup) -> dict:
    """Extract JSON-LD structured data if present."""
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("@type") in (
                        "Article", "BlogPosting", "NewsArticle", "WebPage",
                    ):
                        return item
            elif isinstance(data, dict):
                if data.get("@type") in (
                    "Article", "BlogPosting", "NewsArticle", "WebPage",
                ):
                    return data
        except (json.JSONDecodeError, TypeError):
            continue
    return {}


def extract_author(soup: BeautifulSoup, jsonld: dict) -> str:
    """Extract author from structured data, meta tags, or byline patterns."""
    # JSON-LD
    author = jsonld.get("author", "")
    if isinstance(author, dict):
        author = author.get("name", "")
    if isinstance(author, list) and author:
        author = author[0].get("name", "") if isinstance(author[0], dict) else str(author[0])
    if author:
        return str(author).strip()

    # Meta tags
    meta = _extract_meta(soup, ["author", "article:author", "dc.creator"])
    if meta:
        return meta

    # Visible byline patterns
    for selector in [".author", ".byline", "[rel=author]", ".post-author", ".entry-author"]:
        tag = soup.select_one(selector)
        if tag:
            text = tag.get_text(strip=True)
            # Clean common prefixes
            text = re.sub(r"^(by|written by|author:)\s*", "", text, flags=re.IGNORECASE)
            if text and len(text) < 100:
                return text

    return ""


def extract_date(soup: BeautifulSoup, jsonld: dict) -> str:
    """Extract published date from structured data, meta tags, or time elements."""
    from dateutil import parser as dateparser

    candidates = []

    # JSON-LD dates
    for key in ("datePublished", "dateCreated", "dateModified"):
        val = jsonld.get(key, "")
        if val:
            candidates.append(val)

    # Meta tags
    for name in ["article:published_time", "date", "pubdate",
                  "dc.date", "article:modified_time"]:
        val = _extract_meta(soup, [name])
        if val:
            candidates.append(val)

    # <time> elements
    for time_tag in soup.find_all("time", limit=5):
        dt = time_tag.get("datetime", "")
        if dt:
            candidates.append(dt)

    # Try to parse candidates
    for c in candidates:
        try:
            dt = dateparser.parse(str(c), fuzzy=True)
            if dt:
                return dt.strftime("%Y-%m-%d")
        except (ValueError, OverflowError):
            continue

    return ""


def extract_title(soup: BeautifulSoup, jsonld: dict, readability_title: str) -> str:
    """Extract the best article title."""
    # JSON-LD headline
    jt = jsonld.get("headline", "")
    if jt:
        return str(jt).strip()

    # og:title
    og = _extract_meta(soup, ["og:title", "twitter:title"])
    if og:
        return og

    # Readability's extracted title
    if readability_title:
        return readability_title

    # <h1>
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)

    # <title>
    title_tag = soup.find("title")
    if title_tag:
        return title_tag.get_text(strip=True)

    return ""


# ---------------------------------------------------------------------------
# Content extraction
# ---------------------------------------------------------------------------


def _extract_with_readability(html: str) -> tuple[str, str, float]:
    """Use readability-lxml to extract main content.

    Returns (content_html, title, confidence).
    """
    try:
        doc = Document(html)
        content = doc.summary()
        title = doc.short_title()
        # Rough confidence based on content length
        text = BeautifulSoup(content, "lxml").get_text(strip=True)
        confidence = min(1.0, len(text) / 2000) if text else 0.0
        return content, title, confidence
    except Exception as exc:
        logger.debug("readability extraction failed: %s", exc)
        return "", "", 0.0


def _extract_with_bs4(soup: BeautifulSoup) -> tuple[str, float]:
    """Fallback: extract using semantic tags and heuristics.

    Returns (content_html, confidence).
    """
    # Try semantic containers
    for selector in ["article", "main", "[role=main]",
                     ".post-content", ".entry-content", ".article-body",
                     ".post-body", "#content", ".content"]:
        container = soup.select_one(selector)
        if container:
            text = container.get_text(strip=True)
            if len(text) > 200:
                confidence = min(0.8, len(text) / 3000)
                return str(container), confidence

    # Density heuristic: find the div with the most paragraph text
    best_div = None
    best_len = 0
    for div in soup.find_all(["div", "section"]):
        paragraphs = div.find_all("p")
        total = sum(len(p.get_text(strip=True)) for p in paragraphs)
        if total > best_len:
            best_len = total
            best_div = div

    if best_div and best_len > 200:
        confidence = min(0.6, best_len / 3000)
        return str(best_div), confidence

    return "", 0.0


def _html_to_markdown(content_html: str) -> str:
    """Convert extracted HTML to clean Markdown."""
    soup = BeautifulSoup(content_html, "lxml")

    # Remove unwanted elements
    for tag in soup.find_all(["script", "style", "nav", "footer", "aside",
                              "form", "iframe", "noscript"]):
        tag.decompose()

    lines = []
    for elem in soup.find_all(True):
        if elem.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(elem.name[1])
            text = elem.get_text(strip=True)
            if text:
                lines.append(f"\n{'#' * level} {text}\n")
        elif elem.name == "p":
            text = elem.get_text(strip=True)
            if text:
                lines.append(f"\n{text}\n")
        elif elem.name == "blockquote":
            text = elem.get_text(strip=True)
            if text:
                quoted = "\n".join(f"> {line}" for line in text.split("\n"))
                lines.append(f"\n{quoted}\n")
        elif elem.name == "li":
            text = elem.get_text(strip=True)
            if text:
                lines.append(f"- {text}")
        elif elem.name == "img":
            alt = elem.get("alt", "")
            src = elem.get("src", "")
            if src:
                lines.append(f"\n![{alt}]({src})\n")

    # Deduplicate consecutive blank lines
    md = "\n".join(lines)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


def _html_to_plain(content_html: str) -> str:
    """Convert extracted HTML to plain text preserving paragraph breaks."""
    soup = BeautifulSoup(content_html, "lxml")
    for tag in soup.find_all(["script", "style", "nav", "footer"]):
        tag.decompose()
    text = soup.get_text(separator="\n\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_headings(content_html: str) -> list[str]:
    """Extract heading text from content HTML."""
    soup = BeautifulSoup(content_html, "lxml")
    headings = []
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        text = tag.get_text(strip=True)
        if text and text not in headings:
            headings.append(text)
    return headings


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------


def chunk_text(
    report_id: str,
    plain_text: str,
    headings: list[str],
    min_words: int = 500,
    max_words: int = 1200,
) -> list[dict]:
    """Split plain text into chunks respecting heading boundaries."""
    # Split by headings if they appear in the text
    sections = []
    if headings:
        pattern = "|".join(re.escape(h) for h in headings)
        parts = re.split(f"({pattern})", plain_text)
        current_title = ""
        current_text = ""
        for part in parts:
            if part.strip() in headings:
                if current_text.strip():
                    sections.append((current_title, current_text.strip()))
                current_title = part.strip()
                current_text = ""
            else:
                current_text += part
        if current_text.strip():
            sections.append((current_title, current_text.strip()))
    else:
        sections = [("", plain_text)]

    # Now chunk each section by word count
    chunks = []
    chunk_idx = 0
    for section_title, section_text in sections:
        words = section_text.split()
        if not words:
            continue

        start = 0
        while start < len(words):
            end = min(start + max_words, len(words))

            # Try to find a paragraph break near the target
            if end < len(words):
                chunk_text_candidate = " ".join(words[start:end])
                # Look for a paragraph break in the last 20% of the chunk
                search_start = max(start + min_words, end - (max_words - min_words))
                for i in range(end, search_start, -1):
                    word = words[i - 1] if i <= len(words) else ""
                    if word.endswith((".","!","?","\n")):
                        end = i
                        break

            chunk_words = words[start:end]
            if not chunk_words:
                break

            chunk_idx += 1
            chunk_str = " ".join(chunk_words)
            chunks.append({
                "report_id": report_id,
                "chunk_id": make_chunk_id(report_id, chunk_idx),
                "section_title": section_title,
                "chunk_index": chunk_idx,
                "text": chunk_str,
                "word_count": len(chunk_words),
            })
            start = end

    return chunks


# ---------------------------------------------------------------------------
# Main extraction for one report
# ---------------------------------------------------------------------------


def extract_one(record: dict, base_dir: Path) -> dict:
    """Extract article content from a fetched report. Mutates and returns record."""
    report_id = record["report_id"]
    rdir = raw_dir(base_dir, report_id)
    pdir = processed_dir(base_dir, report_id)

    # Check for existing extraction (resume support)
    article_json_path = pdir / "article.json"
    if article_json_path.exists() and article_json_path.stat().st_size > 0:
        logger.info("%s: already extracted – skipping", report_id)
        record["status"] = "extracted"
        record["article_json_path"] = str(article_json_path.relative_to(base_dir))
        record["article_txt_path"] = str((pdir / "article.txt").relative_to(base_dir))
        record["chunks_path"] = str((pdir / "chunks.jsonl").relative_to(base_dir))
        # Reload metadata from existing article.json
        try:
            existing = read_json(article_json_path)
            record["article_title"] = existing.get("article_title", "")
            record["author"] = existing.get("author", "")
            record["published_date"] = existing.get("published_date", "")
            record["word_count"] = existing.get("word_count", 0)
            record["extraction_method"] = existing.get("extraction_method", "")
            record["extraction_confidence"] = existing.get("extraction_confidence", 0)
        except Exception:
            pass
        return record

    # Determine which HTML to parse
    rendered_path = rdir / "rendered.html"
    source_path = rdir / "source.html"
    if rendered_path.exists() and rendered_path.stat().st_size > 0:
        html_path = rendered_path
    elif source_path.exists() and source_path.stat().st_size > 0:
        html_path = source_path
    else:
        logger.warning("%s: no HTML found – skipping extraction", report_id)
        record["status"] = "failed" if record["status"] == "pending" else record["status"]
        record["notes"] = _append_note(record.get("notes", ""), "No HTML to extract")
        _log_failure(record, base_dir, "parse", "no_html", "No source HTML found")
        return record

    html = html_path.read_text(encoding="utf-8", errors="replace")
    full_soup = BeautifulSoup(html, "lxml")
    jsonld = _extract_jsonld(full_soup)

    # Try readability first, then BS4 fallback
    content_html, rd_title, rd_confidence = _extract_with_readability(html)
    extraction_method = "readability"

    if not content_html or rd_confidence < 0.15:
        bs4_html, bs4_confidence = _extract_with_bs4(full_soup)
        if bs4_confidence > rd_confidence:
            content_html = bs4_html
            rd_confidence = bs4_confidence
            extraction_method = "bs4"
        elif content_html:
            extraction_method = "readability"
        else:
            extraction_method = "bs4_fallback"

    if not content_html:
        logger.warning("%s: extraction produced no content", report_id)
        record["status"] = "partial"
        record["notes"] = _append_note(record.get("notes", ""), "No content extracted")
        _log_failure(record, base_dir, "parse", "parse_failed", "No content extracted from HTML")
        return record

    if extraction_method in ("readability", "bs4"):
        extraction_method = f"{extraction_method}+bs4"

    # Extract metadata
    article_title = extract_title(full_soup, jsonld, rd_title)
    author = extract_author(full_soup, jsonld)
    published_date = extract_date(full_soup, jsonld)
    headings = _extract_headings(content_html)
    language = _extract_meta(full_soup, ["language", "og:locale"]) or "en"
    if len(language) > 5:
        language = language[:2]

    # Convert to markdown and plain text
    markdown = _html_to_markdown(content_html)
    plain_text = _html_to_plain(content_html)
    word_count = len(plain_text.split())

    # Chunk the text
    chunks = chunk_text(report_id, plain_text, headings)

    # Build article.json
    article_data = {
        "report_id": report_id,
        "year": record.get("year", ""),
        "title_seed": record.get("title_seed", ""),
        "source_url": record.get("source_url", ""),
        "final_url": record.get("final_url", ""),
        "source_page": record.get("source_page", ""),
        "domain": record.get("domain", ""),
        "fetch_timestamp_utc": record.get("fetch_timestamp_utc", ""),
        "used_rendering": record.get("used_rendering", False),
        "article_title": article_title,
        "author": author,
        "published_date": published_date,
        "language": language,
        "word_count": word_count,
        "headings": headings,
        "text_markdown_path": str((pdir / "article.md").relative_to(base_dir)),
        "text_plain_path": str((pdir / "article.txt").relative_to(base_dir)),
        "raw_html_path": record.get("raw_html_path", ""),
        "images": [],  # Populated by extract_images stage
        "extraction_method": extraction_method,
        "extraction_confidence": round(rd_confidence, 2),
        "notes": "",
    }

    # Write outputs
    write_json(pdir / "article.json", article_data)
    (pdir / "article.md").write_text(markdown, encoding="utf-8")
    (pdir / "article.txt").write_text(plain_text, encoding="utf-8")

    # Write chunks
    with open(pdir / "chunks.jsonl", "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    # Update record
    record["status"] = "extracted"
    record["article_title"] = article_title
    record["author"] = author
    record["published_date"] = published_date
    record["language"] = language
    record["word_count"] = word_count
    record["extraction_method"] = extraction_method
    record["extraction_confidence"] = round(rd_confidence, 2)
    record["article_json_path"] = str((pdir / "article.json").relative_to(base_dir))
    record["article_txt_path"] = str((pdir / "article.txt").relative_to(base_dir))
    record["chunks_path"] = str((pdir / "chunks.jsonl").relative_to(base_dir))

    logger.info(
        "%s: extracted %d words, method=%s, confidence=%.2f",
        report_id, word_count, extraction_method, rd_confidence,
    )
    return record


def _append_note(existing: str, note: str) -> str:
    return f"{existing}; {note}" if existing else note


def _log_failure(record: dict, base_dir: Path, stage: str, err_type: str, err_msg: str):
    failed_path = manifests_dir(base_dir) / "failed_urls.csv"
    append_csv_row(failed_path, {
        "report_id": record["report_id"],
        "url": record.get("normalized_url", ""),
        "final_url": record.get("final_url", ""),
        "failure_stage": stage,
        "error_type": err_type,
        "error_message": err_msg,
        "retry_recommended": "false",
    }, FAILED_URLS_COLUMNS)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run(
    records: list[dict],
    base_dir: Path,
    *,
    limit: int | None = None,
    report_id_filter: str | None = None,
) -> list[dict]:
    """Extract articles for all fetched records."""
    targets = [r for r in records if r["status"] in ("fetched", "extracted")]
    if report_id_filter:
        targets = [r for r in targets if r["report_id"] == report_id_filter]
    if limit:
        targets = targets[:limit]

    for i, record in enumerate(targets, 1):
        logger.info("Extracting %d/%d: %s", i, len(targets), record["report_id"])
        try:
            extract_one(record, base_dir)
        except Exception as exc:
            logger.error("%s: extraction error – %s", record["report_id"], exc)
            record["status"] = "partial"
            record["notes"] = _append_note(
                record.get("notes", ""), f"Extraction error: {exc}"
            )
            _log_failure(record, base_dir, "parse", "parse_failed", str(exc)[:500])

    extracted = sum(1 for r in records if r["status"] == "extracted")
    partial = sum(1 for r in records if r["status"] == "partial")
    logger.info("Extraction complete: %d extracted, %d partial", extracted, partial)
    return records


def main():
    parser = argparse.ArgumentParser(description="Stage 4: Extract article text")
    parser.add_argument("--input", required=True, help="Path to input CSV")
    parser.add_argument("--out", default="hardrock_reports", help="Base output directory")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    from scripts.normalize_input import run as normalize_run
    from scripts.utils import setup_logging

    setup_logging(args.verbose)
    records, _ = normalize_run(Path(args.input), Path(args.out))
    # Mark fetched ones
    for r in records:
        rdir = raw_dir(Path(args.out), r["report_id"])
        if (rdir / "source.html").exists():
            r["status"] = "fetched"
    run(records, Path(args.out), limit=args.limit)


if __name__ == "__main__":
    main()
