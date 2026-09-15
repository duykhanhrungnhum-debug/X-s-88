"""Application pipeline enforcing the Xoso88 data lifecycle."""
from __future__ import annotations

from dataclasses import replace

from .models import LotteryResult, ResultStatus
from .validator import validate_prizes


def validate_result(result: LotteryResult) -> LotteryResult:
    """Return a VALIDATED result only when all structural checks pass."""
    if not result.province.strip():
        raise ValueError("province is required")
    if not result.draw_date.strip():
        raise ValueError("draw_date is required")
    if not result.source_url.startswith("https://"):
        raise ValueError("source_url must use HTTPS")
    if not validate_prizes(result.prizes):
        raise ValueError("prizes failed structural validation")
    return replace(result, status=ResultStatus.VALIDATED)


def publish_validated_result(store, result: LotteryResult, *, province_code: str, region: str, source_fetch_id: str | None = None) -> str:
    """Persist only a result that has passed the validation boundary."""
    if result.status is not ResultStatus.VALIDATED:
        raise ValueError("publish requires a VALIDATED result")
    return store.publish_validated_result(
        result,
        province_code=province_code,
        region=region,
        source_fetch_id=source_fetch_id,
    )
