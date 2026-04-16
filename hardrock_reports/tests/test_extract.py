"""Tests for extract_articles.py – article extraction from HTML."""

import json
import tempfile
from pathlib import Path

import pytest

from scripts.extract_articles import (
    _extract_with_readability,
    _extract_with_bs4,
    _html_to_markdown,
    _html_to_plain,
    _extract_headings,
    chunk_text,
    extract_author,
    extract_date,
    extract_title,
    extract_one,
)
from scripts.utils import ensure_dir, write_json


# ---------------------------------------------------------------------------
# HTML fixtures
# ---------------------------------------------------------------------------

SAMPLE_ARTICLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>My Hardrock 100 Race Report</title>
    <meta name="author" content="Jane Runner">
    <meta property="article:published_time" content="2025-07-20T10:00:00Z">
    <meta property="og:title" content="My Hardrock 100 Race Report – 2025">
</head>
<body>
<nav>Navigation links here</nav>
<article>
    <h1>My Hardrock 100 Race Report</h1>
    <p class="byline">By Jane Runner</p>
    <h2>Before the Race</h2>
    <p>I had been training for months in the mountains of Colorado.
    The anticipation was building as we drove into Silverton on Thursday
    afternoon. The town was buzzing with runners, crews, and pacers.
    I checked my gear multiple times, making sure everything was ready
    for the long journey ahead.</p>
    <h2>The Start</h2>
    <p>At 6:00 AM on Friday, we lined up at the start in Silverton.
    The energy was electric. The course record holder gave a brief speech.
    Then the gun went off and we started climbing out of town toward
    Dives-Little Giant Pass. The first climb was steep but manageable,
    and I settled into a comfortable rhythm.</p>
    <p>The views from the top were absolutely stunning. You could see
    for miles in every direction, with snow-capped peaks stretching
    to the horizon. This is why we run these mountains.</p>
    <h2>The Night Section</h2>
    <p>As darkness fell around mile 60, I put on my headlamp and
    pressed forward. The trail through Kroger's Canteen was rocky
    and technical. My pacer joined me at Ouray and kept me moving
    through the long night. We talked about everything and nothing,
    just trying to stay awake and keep moving forward.</p>
    <blockquote>The mountains don't care about your training plan.</blockquote>
    <figure>
        <img src="https://example.com/hardrock-finish.jpg" alt="Crossing the finish line">
        <figcaption>The moment I crossed the finish line in Silverton</figcaption>
    </figure>
</article>
<footer>Site footer content</footer>
</body>
</html>
"""

MINIMAL_HTML = """
<html>
<body>
<div class="entry-content">
<p>This is a race report about running the Hardrock 100. I drove into Silverton
the day before and checked into my hotel. The mountains loomed above, reminding me
of the challenge ahead. After a restless night of sleep, I woke up at four in the
morning to prepare my gear and eat a quick breakfast.</p>
<p>I ran the Hardrock 100 and it was the hardest thing I have ever done.
The climbs were brutal, the descents were technical, and the altitude made
everything twice as difficult. But crossing that finish line made it all worthwhile.</p>
</div>
</body>
</html>
"""

EMPTY_HTML = """
<html>
<body>
<script>window.location='https://example.com';</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Readability extraction
# ---------------------------------------------------------------------------

class TestReadabilityExtraction:
    def test_extracts_content(self):
        html, title, confidence = _extract_with_readability(SAMPLE_ARTICLE_HTML)
        assert html  # non-empty
        assert confidence > 0

    def test_empty_page_low_confidence(self):
        html, title, confidence = _extract_with_readability(EMPTY_HTML)
        # Either empty content or very low confidence
        assert confidence < 0.2 or html == ""


# ---------------------------------------------------------------------------
# BS4 fallback extraction
# ---------------------------------------------------------------------------

class TestBs4Extraction:
    def test_finds_article_tag(self):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(SAMPLE_ARTICLE_HTML, "lxml")
        content, confidence = _extract_with_bs4(soup)
        assert content
        assert confidence > 0

    def test_finds_entry_content(self):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(MINIMAL_HTML, "lxml")
        content, confidence = _extract_with_bs4(soup)
        assert content
        assert "race report" in content.lower()


# ---------------------------------------------------------------------------
# Content conversion
# ---------------------------------------------------------------------------

class TestHtmlToMarkdown:
    def test_headings_converted(self):
        md = _html_to_markdown("<h2>My Section</h2><p>Content here.</p>")
        assert "## My Section" in md
        assert "Content here." in md

    def test_blockquotes(self):
        md = _html_to_markdown("<blockquote>A wise saying</blockquote>")
        assert "> A wise saying" in md


class TestHtmlToPlain:
    def test_returns_text(self):
        plain = _html_to_plain(SAMPLE_ARTICLE_HTML)
        assert "Silverton" in plain
        assert len(plain) > 100

    def test_removes_nav_footer(self):
        plain = _html_to_plain(SAMPLE_ARTICLE_HTML)
        assert "Navigation links" not in plain
        assert "Site footer" not in plain


class TestExtractHeadings:
    def test_finds_headings(self):
        headings = _extract_headings(SAMPLE_ARTICLE_HTML)
        assert "Before the Race" in headings or "The Start" in headings


# ---------------------------------------------------------------------------
# Metadata extraction
# ---------------------------------------------------------------------------

class TestExtractAuthor:
    def test_from_meta_tag(self):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(SAMPLE_ARTICLE_HTML, "lxml")
        author = extract_author(soup, {})
        assert author == "Jane Runner"

    def test_from_jsonld(self):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup("<html><body></body></html>", "lxml")
        author = extract_author(soup, {"author": {"name": "John Doe"}})
        assert author == "John Doe"


class TestExtractDate:
    def test_from_meta_tag(self):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(SAMPLE_ARTICLE_HTML, "lxml")
        date = extract_date(soup, {})
        assert date == "2025-07-20"


class TestExtractTitle:
    def test_from_og_title(self):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(SAMPLE_ARTICLE_HTML, "lxml")
        title = extract_title(soup, {}, "")
        assert "Hardrock" in title


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

class TestChunking:
    def test_produces_chunks(self):
        text = " ".join(["word"] * 2000)
        chunks = chunk_text("HR_2025_001", text, [])
        assert len(chunks) >= 2
        for c in chunks:
            assert c["report_id"] == "HR_2025_001"
            assert c["chunk_id"].startswith("HR_2025_001_CH_")
            assert c["word_count"] > 0
            assert c["word_count"] <= 1200

    def test_short_text_single_chunk(self):
        text = "A short race report about running."
        chunks = chunk_text("HR_2025_001", text, [])
        assert len(chunks) == 1

    def test_respects_headings(self):
        text = "Intro text. Before the Race More text here. The Start Even more text."
        headings = ["Before the Race", "The Start"]
        chunks = chunk_text("HR_2025_001", text, headings)
        assert len(chunks) >= 1
        # Section titles should be captured
        titles = [c["section_title"] for c in chunks]
        assert any(t in titles for t in ["", "Before the Race", "The Start"])


# ---------------------------------------------------------------------------
# Full extraction integration (with filesystem)
# ---------------------------------------------------------------------------

class TestExtractOne:
    def test_full_extraction(self, tmp_path):
        report_id = "HR_2025_001"
        base_dir = tmp_path
        rdir = ensure_dir(base_dir / "raw" / report_id)
        pdir = ensure_dir(base_dir / "processed" / report_id)
        ensure_dir(base_dir / "manifests")

        # Write source HTML
        (rdir / "source.html").write_text(SAMPLE_ARTICLE_HTML, encoding="utf-8")

        record = {
            "report_id": report_id,
            "year": 2025,
            "title_seed": "Test Report",
            "source_url": "https://example.com/report",
            "final_url": "https://example.com/report",
            "source_page": "",
            "domain": "example.com",
            "status": "fetched",
            "raw_html_path": f"raw/{report_id}/source.html",
            "fetch_timestamp_utc": "2026-01-01T00:00:00Z",
            "used_rendering": False,
            "notes": "",
            "normalized_url": "https://example.com/report",
        }

        result = extract_one(record, base_dir)

        assert result["status"] == "extracted"
        assert result["word_count"] > 0
        assert result["extraction_method"]
        assert (pdir / "article.json").exists()
        assert (pdir / "article.txt").exists()
        assert (pdir / "article.md").exists()
        assert (pdir / "chunks.jsonl").exists()

        # Check article.json structure
        import json
        article = json.loads((pdir / "article.json").read_text())
        assert article["report_id"] == report_id
        assert article["word_count"] > 0
        assert isinstance(article["headings"], list)

    def test_missing_html_handled(self, tmp_path):
        report_id = "HR_2025_002"
        base_dir = tmp_path
        ensure_dir(base_dir / "raw" / report_id)
        ensure_dir(base_dir / "manifests")

        record = {
            "report_id": report_id,
            "year": 2025,
            "title_seed": "Missing",
            "source_url": "https://example.com/missing",
            "final_url": "",
            "source_page": "",
            "domain": "example.com",
            "status": "fetched",
            "raw_html_path": "",
            "notes": "",
            "normalized_url": "https://example.com/missing",
        }

        result = extract_one(record, base_dir)
        # Should not crash, should mark appropriately
        assert result["status"] in ("failed", "fetched")
