from datetime import datetime, timezone

import pytest

from scraper.models import LotteryResult, ResultStatus
from scraper.pipeline import validate_result


def sample_result(status=ResultStatus.PARSED):
    return LotteryResult(
        province="Tây Ninh",
        draw_date="2026-09-15",
        prizes={"Giải nhất": ["12345"], "Giải Đặc Biệt": ["01234"]},
        source_url="https://example.test/result",
        fetched_at=datetime.now(timezone.utc),
        status=status,
    )


def test_validation_promotes_parsed_result():
    result = validate_result(sample_result())
    assert result.status is ResultStatus.VALIDATED
    assert result.prizes["Giải Đặc Biệt"] == ["01234"]


def test_validation_rejects_http_source():
    result = sample_result()
    result = LotteryResult(**{**result.__dict__, "source_url": "http://example.test/result"})
    with pytest.raises(ValueError, match="HTTPS"):
        validate_result(result)


def test_validation_rejects_non_numeric_number():
    result = sample_result()
    result = LotteryResult(**{**result.__dict__, "prizes": {"Giải nhất": ["12A45"]}})
    with pytest.raises(ValueError, match="structural"):
        validate_result(result)
