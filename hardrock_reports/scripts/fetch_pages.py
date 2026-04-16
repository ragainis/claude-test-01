"""Stage 2 & 3: Fetch raw pages (HTTP + optional rendering fallback)."""

import argparse
import json
import logging
import time
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

from scripts.utils import (
    CRAWL_LOG_COLUMNS,
    FAILED_URLS_COLUMNS,
    append_csv_row,
    ensure_dir,
    manifests_dir,
    raw_dir,
    utc_now_iso,
    write_json,
)

logger = logging.getLogger("hardrock.fetch")

USER_AGENT = (
    "HardrockCorpusBot/1.0 "
    "(research extraction; +https://github.com/ragainis/claude-test-01)"
)
TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0  # seconds base
RATE_LIMIT_DELAY = 1.5  # seconds between requests
MIN_BODY_LENGTH = 500  # chars – below this, page may need rendering


def _classify_error(exc: Exception) -> tuple[str, str]:
    """Classify an exception into (error_type, error_message)."""
    name = type(exc).__name__
    if isinstance(exc, httpx.TimeoutException):
        return "timeout", str(exc)
    if isinstance(exc, httpx.ConnectError):
        return "connection_error", str(exc)
    if isinstance(exc, httpx.TooManyRedirects):
        return "redirect_error", str(exc)
    return name, str(exc)


def _status_error_type(code: int) -> str:
    if code == 403:
        return "403_forbidden"
    if code == 404:
        return "404_not_found"
    if 500 <= code < 600:
        return "5xx_server_error"
    return f"http_{code}"


def _build_redirect_chain(response: httpx.Response) -> str:
    """Serialize the redirect chain as a JSON-encoded list of URLs."""
    chain = [str(r.url) for r in response.history]
    if chain:
        chain.append(str(response.url))
    return json.dumps(chain) if chain else "[]"


def _body_looks_empty(html: str) -> bool:
    """Check whether the fetched HTML body appears too thin for extraction."""
    soup = BeautifulSoup(html, "lxml")
    body = soup.find("body")
    if body is None:
        return True
    text = body.get_text(separator=" ", strip=True)
    return len(text) < MIN_BODY_LENGTH


def fetch_one(
    record: dict,
    base_dir: Path,
    *,
    skip_render: bool = False,
    refetch: bool = False,
) -> dict:
    """Fetch a single URL. Mutates and returns the record dict."""
    report_id = record["report_id"]
    url = record["normalized_url"]
    rdir = raw_dir(base_dir, report_id)

    # Resume: skip if already fetched successfully
    html_path = rdir / "source.html"
    if html_path.exists() and html_path.stat().st_size > 0 and not refetch:
        logger.info("%s: already fetched – skipping", report_id)
        record["status"] = max_status(record.get("status", "pending"), "fetched")
        record["raw_html_path"] = str(html_path.relative_to(base_dir))
        return record

    crawl_log_path = manifests_dir(base_dir) / "crawl_log.csv"
    failed_path = manifests_dir(base_dir) / "failed_urls.csv"

    last_error_type = ""
    last_error_msg = ""
    response = None

    for attempt in range(1, MAX_RETRIES + 1):
        start_ts = utc_now_iso()
        start_time = time.monotonic()
        try:
            with httpx.Client(
                follow_redirects=True,
                timeout=TIMEOUT,
                headers={"User-Agent": USER_AGENT},
                max_redirects=10,
            ) as client:
                response = client.get(url)

            duration = round(time.monotonic() - start_time, 2)
            redirect_chain = _build_redirect_chain(response)

            # Log the crawl attempt
            append_csv_row(crawl_log_path, {
                "report_id": report_id,
                "attempt": attempt,
                "timestamp_utc": start_ts,
                "url": url,
                "method": "GET",
                "status_code": response.status_code,
                "used_rendering": False,
                "duration_seconds": duration,
                "redirect_chain": redirect_chain,
                "error_type": "",
                "error_message": "",
            }, CRAWL_LOG_COLUMNS)

            if response.status_code >= 400:
                last_error_type = _status_error_type(response.status_code)
                last_error_msg = f"HTTP {response.status_code}"
                if response.status_code < 500:
                    # Client errors: don't retry
                    break
                # Server errors: retry
                logger.warning(
                    "%s: attempt %d got %d – retrying",
                    report_id, attempt, response.status_code,
                )
                time.sleep(RETRY_BACKOFF * attempt)
                continue

            # Success
            break

        except Exception as exc:
            duration = round(time.monotonic() - start_time, 2)
            last_error_type, last_error_msg = _classify_error(exc)
            logger.warning(
                "%s: attempt %d failed (%s) – %s",
                report_id, attempt, last_error_type, last_error_msg,
            )
            append_csv_row(crawl_log_path, {
                "report_id": report_id,
                "attempt": attempt,
                "timestamp_utc": start_ts,
                "url": url,
                "method": "GET",
                "status_code": "",
                "used_rendering": False,
                "duration_seconds": duration,
                "redirect_chain": "[]",
                "error_type": last_error_type,
                "error_message": last_error_msg[:500],
            }, CRAWL_LOG_COLUMNS)
            time.sleep(RETRY_BACKOFF * attempt)
            response = None
            continue

    # Evaluate result
    if response is None or response.status_code >= 400:
        record["status"] = "failed"
        record["fetch_status_code"] = response.status_code if response else ""
        record["fetch_timestamp_utc"] = utc_now_iso()
        record["notes"] = append_note(
            record.get("notes", ""),
            f"Fetch failed: {last_error_type} – {last_error_msg}",
        )
        append_csv_row(failed_path, {
            "report_id": report_id,
            "url": url,
            "final_url": str(response.url) if response else "",
            "failure_stage": "fetch",
            "error_type": last_error_type,
            "error_message": last_error_msg[:500],
            "retry_recommended": "true" if last_error_type in (
                "timeout", "connection_error", "5xx_server_error"
            ) else "false",
        }, FAILED_URLS_COLUMNS)
        return record

    # Save raw artifacts
    html_content = response.text
    final_url = str(response.url)

    write_json(rdir / "request.json", {
        "url": url,
        "method": "GET",
        "headers": {"User-Agent": USER_AGENT},
        "timestamp_utc": utc_now_iso(),
    })

    write_json(rdir / "response_headers.json", dict(response.headers))

    (rdir / "source.html").write_text(html_content, encoding="utf-8")

    # Plain-text dump from raw HTML
    soup = BeautifulSoup(html_content, "lxml")
    plain = soup.get_text(separator="\n", strip=True)
    (rdir / "source.txt").write_text(plain, encoding="utf-8")

    record["final_url"] = final_url
    record["fetch_status_code"] = response.status_code
    record["fetch_timestamp_utc"] = utc_now_iso()
    record["raw_html_path"] = str((rdir / "source.html").relative_to(base_dir))
    record["status"] = "fetched"
    record["used_rendering"] = False

    # Check if rendering might be needed
    needs_render = _body_looks_empty(html_content)
    if needs_render and not skip_render:
        logger.info("%s: body looks thin – attempting rendering fallback", report_id)
        rendered = _try_render(record, base_dir)
        if rendered:
            record["used_rendering"] = True

    logger.info(
        "%s: fetched (%d) from %s",
        report_id, response.status_code, final_url[:80],
    )
    return record


def _try_render(record: dict, base_dir: Path) -> bool:
    """Attempt headless browser rendering. Returns True if successful."""
    report_id = record["report_id"]
    url = record.get("final_url") or record["normalized_url"]
    rdir = raw_dir(base_dir, report_id)
    crawl_log_path = manifests_dir(base_dir) / "crawl_log.csv"
    failed_path = manifests_dir(base_dir) / "failed_urls.csv"

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("%s: playwright not installed – skipping render", report_id)
        record["notes"] = append_note(
            record.get("notes", ""), "Rendering skipped: playwright not installed"
        )
        return False

    start_ts = utc_now_iso()
    start_time = time.monotonic()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=USER_AGENT)
            page.goto(url, wait_until="networkidle", timeout=45000)
            rendered_html = page.content()
            # Save screenshot for debugging
            page.screenshot(path=str(rdir / "screenshot.png"), full_page=False)
            browser.close()

        duration = round(time.monotonic() - start_time, 2)
        (rdir / "rendered.html").write_text(rendered_html, encoding="utf-8")

        append_csv_row(crawl_log_path, {
            "report_id": report_id,
            "attempt": 1,
            "timestamp_utc": start_ts,
            "url": url,
            "method": "RENDER",
            "status_code": 200,
            "used_rendering": True,
            "duration_seconds": duration,
            "redirect_chain": "[]",
            "error_type": "",
            "error_message": "",
        }, CRAWL_LOG_COLUMNS)

        logger.info("%s: rendered successfully (%.1fs)", report_id, duration)
        return True

    except Exception as exc:
        duration = round(time.monotonic() - start_time, 2)
        err_type = "render_failed"
        err_msg = str(exc)[:500]
        logger.warning("%s: render failed – %s", report_id, err_msg)

        append_csv_row(crawl_log_path, {
            "report_id": report_id,
            "attempt": 1,
            "timestamp_utc": start_ts,
            "url": url,
            "method": "RENDER",
            "status_code": "",
            "used_rendering": True,
            "duration_seconds": duration,
            "redirect_chain": "[]",
            "error_type": err_type,
            "error_message": err_msg,
        }, CRAWL_LOG_COLUMNS)

        record["notes"] = append_note(
            record.get("notes", ""), f"Render failed: {err_msg}"
        )
        return False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_STATUS_ORDER = {"pending": 0, "fetched": 1, "extracted": 2, "partial": 1, "failed": -1}


def max_status(current: str, new: str) -> str:
    """Return the higher-priority status."""
    if _STATUS_ORDER.get(new, 0) > _STATUS_ORDER.get(current, 0):
        return new
    return current


def append_note(existing: str, note: str) -> str:
    if existing:
        return f"{existing}; {note}"
    return note


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run(
    records: list[dict],
    base_dir: Path,
    *,
    skip_render: bool = False,
    refetch: bool = False,
    limit: int | None = None,
    report_id_filter: str | None = None,
) -> list[dict]:
    """Fetch pages for all records. Returns mutated records."""
    targets = records
    if report_id_filter:
        targets = [r for r in records if r["report_id"] == report_id_filter]
    if limit:
        # Only limit the ones we actually need to fetch
        pending = [r for r in targets if r["status"] in ("pending", "failed") or refetch]
        already_done = [r for r in targets if r not in pending]
        targets = already_done + pending[:limit]

    total = len(targets)
    for i, record in enumerate(targets, 1):
        if record["status"] == "failed" and not refetch:
            continue
        logger.info("Fetching %d/%d: %s", i, total, record["report_id"])
        fetch_one(record, base_dir, skip_render=skip_render, refetch=refetch)
        time.sleep(RATE_LIMIT_DELAY)

    fetched = sum(1 for r in records if r["status"] in ("fetched", "extracted"))
    failed = sum(1 for r in records if r["status"] == "failed")
    logger.info("Fetch complete: %d fetched, %d failed out of %d", fetched, failed, len(records))
    return records


def main():
    parser = argparse.ArgumentParser(description="Stage 2: Fetch raw pages")
    parser.add_argument("--input", required=True, help="Path to input CSV")
    parser.add_argument("--out", default="hardrock_reports", help="Base output directory")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--skip-render", action="store_true")
    parser.add_argument("--refetch", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    from scripts.normalize_input import run as normalize_run
    from scripts.utils import setup_logging

    setup_logging(args.verbose)
    records, _ = normalize_run(Path(args.input), Path(args.out))
    run(records, Path(args.out), skip_render=args.skip_render,
        refetch=args.refetch, limit=args.limit)


if __name__ == "__main__":
    main()
