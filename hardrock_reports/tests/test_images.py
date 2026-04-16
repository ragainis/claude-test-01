"""Tests for extract_images.py – image extraction and URL handling."""

import pytest

from scripts.extract_images import find_content_images
from scripts.utils import looks_decorative, make_image_id


# ---------------------------------------------------------------------------
# Image ID generation
# ---------------------------------------------------------------------------

class TestMakeImageId:
    def test_format(self):
        assert make_image_id("HR_2025_001", 1) == "HR_2025_001_IMG_001"
        assert make_image_id("HR_2025_001", 42) == "HR_2025_001_IMG_042"


# ---------------------------------------------------------------------------
# Decorative image detection
# ---------------------------------------------------------------------------

class TestLooksDecorative:
    def test_logo_in_url(self):
        assert looks_decorative("https://example.com/images/site-logo.png")

    def test_icon_in_url(self):
        assert looks_decorative("https://example.com/assets/icon-share.svg")

    def test_avatar(self):
        assert looks_decorative("https://example.com/avatar-small.jpg")

    def test_tracking_pixel(self):
        assert looks_decorative("https://tracking.example.com/pixel.gif")

    def test_normal_photo(self):
        assert not looks_decorative("https://example.com/photos/mountain-view.jpg")

    def test_small_dimensions(self):
        assert looks_decorative("https://example.com/img.jpg", width=50, height=50)

    def test_normal_dimensions(self):
        assert not looks_decorative("https://example.com/img.jpg", width=800, height=600)


# ---------------------------------------------------------------------------
# Image finding in HTML
# ---------------------------------------------------------------------------

ARTICLE_WITH_IMAGES = """
<html>
<body>
<nav><img src="/logo.png" alt="Site Logo"></nav>
<article>
    <h1>Race Report</h1>
    <p>Starting the race at dawn.</p>
    <figure>
        <img src="/photos/start-line.jpg" alt="Start line at Silverton"
             width="800" height="600">
        <figcaption>The start line at 6 AM</figcaption>
    </figure>
    <p>Running through the mountains.</p>
    <img src="trail-photo.jpg" alt="Mountain trail">
    <img src="/assets/share-icon.svg" alt="Share" width="24" height="24">
    <img src="/photos/finish.jpg" alt="Finish line">
</article>
<footer>
    <img src="/footer-badge.png" alt="Badge">
</footer>
</body>
</html>
"""

ARTICLE_WITH_RELATIVE_URLS = """
<html><body>
<article>
    <img src="../images/photo.jpg" alt="A photo">
    <img src="//cdn.example.com/pic.png" alt="CDN image">
    <img src="local.jpg" alt="Local">
</article>
</body></html>
"""


class TestFindContentImages:
    def test_finds_article_images(self):
        images = find_content_images(
            ARTICLE_WITH_IMAGES, "https://example.com/race-report"
        )
        urls = [img["image_url"] for img in images]
        # Should find content images
        assert any("start-line.jpg" in u for u in urls)
        assert any("trail-photo.jpg" in u for u in urls)
        assert any("finish.jpg" in u for u in urls)

    def test_extracts_alt_text(self):
        images = find_content_images(
            ARTICLE_WITH_IMAGES, "https://example.com/race-report"
        )
        start_img = [i for i in images if "start-line" in i["image_url"]]
        assert start_img
        assert start_img[0]["alt_text"] == "Start line at Silverton"

    def test_extracts_caption(self):
        images = find_content_images(
            ARTICLE_WITH_IMAGES, "https://example.com/race-report"
        )
        start_img = [i for i in images if "start-line" in i["image_url"]]
        assert start_img
        assert "6 AM" in start_img[0]["caption"]

    def test_marks_decorative(self):
        images = find_content_images(
            ARTICLE_WITH_IMAGES, "https://example.com/race-report"
        )
        share_icon = [i for i in images if "share-icon" in i["image_url"]]
        assert share_icon
        assert share_icon[0]["is_decorative"] is True

    def test_resolves_relative_urls(self):
        images = find_content_images(
            ARTICLE_WITH_RELATIVE_URLS, "https://example.com/reports/page.html"
        )
        urls = [img["image_url"] for img in images]
        # All URLs should be absolute
        for url in urls:
            assert url.startswith("http")
        # Relative should be resolved
        assert any("example.com/images/photo.jpg" in u for u in urls)
        assert any("cdn.example.com/pic.png" in u for u in urls)

    def test_no_duplicates(self):
        html = """
        <article>
            <img src="/photo.jpg" alt="Photo">
            <img src="/photo.jpg" alt="Photo again">
        </article>
        """
        images = find_content_images(html, "https://example.com/")
        urls = [img["image_url"] for img in images]
        assert len(urls) == len(set(urls))

    def test_empty_article(self):
        html = "<html><body><article><p>No images here.</p></article></body></html>"
        images = find_content_images(html, "https://example.com/")
        assert images == []
