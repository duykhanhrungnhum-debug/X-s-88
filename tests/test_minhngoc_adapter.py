from datetime import date

import pytest

from scraper.sources.minhngoc import (
    PRIZE_ORDER,
    build_source_url,
    extract_result_rows,
    normalize_number,
)


def test_normalize_number_preserves_leading_zeroes():
    assert normalize_number(" 00123 ") == "00123"


def test_normalize_number_rejects_non_numeric_values():
    with pytest.raises(ValueError):
        normalize_number("12A")


def test_build_source_url():
    assert build_source_url(date(2026, 9, 14)).endswith("14-09-2026.html")


def test_extract_result_rows():
    rows = extract_result_rows(
        [
            {
                "province": "Tây Ninh",
                "region": "Nam",
                "prize": "Giải Đặc Biệt",
                "numbers": ["910457"],
            }
        ]
    )
    assert rows[0].province == "Tây Ninh"
    assert rows[0].numbers == ("910457",)
    assert "Giải Đặc Biệt" in PRIZE_ORDER
