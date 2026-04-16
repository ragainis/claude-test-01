"""Tests for normalize_input.py – CSV normalization and ID assignment."""

import csv
import tempfile
from pathlib import Path

import pytest

from scripts.normalize_input import normalize_rows, read_input_csv
from scripts.utils import extract_domain, is_valid_url, make_report_id, normalize_url


# ---------------------------------------------------------------------------
# URL normalization
# ---------------------------------------------------------------------------

class TestNormalizeUrl:
    def test_strips_whitespace(self):
        assert normalize_url("  https://example.com  ") == "https://example.com"

    def test_adds_scheme(self):
        result = normalize_url("example.com/path")
        assert result.startswith("https://")

    def test_lowercases_domain(self):
        assert "example.com" in normalize_url("https://EXAMPLE.COM/Path")

    def test_removes_fragment(self):
        result = normalize_url("https://example.com/page#section")
        assert "#" not in result

    def test_preserves_query(self):
        result = normalize_url("https://example.com/page?id=42")
        assert "?id=42" in result

    def test_removes_trailing_slash(self):
        result = normalize_url("https://example.com/path/")
        assert result == "https://example.com/path"

    def test_preserves_root_slash(self):
        result = normalize_url("https://example.com/")
        assert result.endswith("/")

    def test_empty_string(self):
        assert normalize_url("") == ""


class TestExtractDomain:
    def test_basic(self):
        assert extract_domain("https://www.example.com/path") == "example.com"

    def test_no_www(self):
        assert extract_domain("https://blog.example.com/path") == "blog.example.com"

    def test_invalid(self):
        assert extract_domain("not-a-url") == ""


class TestIsValidUrl:
    def test_valid(self):
        assert is_valid_url("https://example.com/page")

    def test_invalid_no_scheme(self):
        assert not is_valid_url("example.com")

    def test_invalid_empty(self):
        assert not is_valid_url("")


# ---------------------------------------------------------------------------
# ID generation
# ---------------------------------------------------------------------------

class TestMakeReportId:
    def test_format(self):
        assert make_report_id(2025, 1) == "HR_2025_001"
        assert make_report_id(2025, 12) == "HR_2025_012"
        assert make_report_id(2018, 100) == "HR_2018_100"


# ---------------------------------------------------------------------------
# CSV reading
# ---------------------------------------------------------------------------

class TestReadInputCsv:
    def test_reads_valid_csv(self, tmp_path):
        csv_path = tmp_path / "input.csv"
        csv_path.write_text(
            "year,title,url,source_page\n"
            "2025,Test Report,https://example.com/report,https://hardrock100.com\n"
        )
        rows = read_input_csv(csv_path)
        assert len(rows) == 1
        assert rows[0]["year"] == "2025"
        assert rows[0]["title"] == "Test Report"

    def test_raises_on_missing_columns(self, tmp_path):
        csv_path = tmp_path / "bad.csv"
        csv_path.write_text("year,title\n2025,Test\n")
        with pytest.raises(ValueError, match="missing required columns"):
            read_input_csv(csv_path)


# ---------------------------------------------------------------------------
# Normalization pipeline
# ---------------------------------------------------------------------------

class TestNormalizeRows:
    def _make_rows(self, rows):
        return [
            {"year": r[0], "title": r[1], "url": r[2], "source_page": r[3]}
            for r in rows
        ]

    def test_assigns_stable_ids(self):
        rows = self._make_rows([
            ("2025", "Report A", "https://example.com/a", "https://hardrock100.com"),
            ("2025", "Report B", "https://example.com/b", "https://hardrock100.com"),
            ("2024", "Report C", "https://example.com/c", "https://hardrock100.com"),
        ])
        records, failures = normalize_rows(rows)
        assert len(records) == 3
        assert records[0]["report_id"] == "HR_2025_001"
        assert records[1]["report_id"] == "HR_2025_002"
        assert records[2]["report_id"] == "HR_2024_001"

    def test_ids_stable_on_rerun(self):
        rows = self._make_rows([
            ("2025", "A", "https://example.com/a", ""),
            ("2025", "B", "https://example.com/b", ""),
        ])
        r1, _ = normalize_rows(rows)
        r2, _ = normalize_rows(rows)
        assert [r["report_id"] for r in r1] == [r["report_id"] for r in r2]

    def test_malformed_url_logged_not_dropped(self):
        rows = self._make_rows([
            ("2025", "Good", "https://example.com/good", ""),
            ("2025", "Bad", "", ""),
        ])
        records, failures = normalize_rows(rows)
        # Bad URL still creates a record (status=failed) + a failure entry
        assert len(records) == 2
        assert len(failures) == 1
        assert failures[0]["error_type"] == "invalid_url"
        failed_record = [r for r in records if r["status"] == "failed"]
        assert len(failed_record) == 1

    def test_invalid_year_logged(self):
        rows = self._make_rows([
            ("abc", "Title", "https://example.com", ""),
        ])
        records, failures = normalize_rows(rows)
        assert len(records) == 0
        assert len(failures) == 1
        assert failures[0]["error_type"] == "invalid_year"

    def test_preserves_source_url(self):
        original = "  https://Example.COM/path/  "
        rows = self._make_rows([
            ("2025", "Title", original, ""),
        ])
        records, _ = normalize_rows(rows)
        assert records[0]["source_url"] == original.strip()
        assert records[0]["normalized_url"] != original.strip()

    def test_domain_extracted(self):
        rows = self._make_rows([
            ("2025", "Title", "https://www.irunfar.com/report", ""),
        ])
        records, _ = normalize_rows(rows)
        assert records[0]["domain"] == "irunfar.com"
