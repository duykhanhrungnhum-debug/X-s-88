from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class ResultStatus(StrEnum):
    FETCHED = "FETCHED"
    PARSED = "PARSED"
    VALIDATED = "VALIDATED"
    PUBLISHED = "PUBLISHED"


@dataclass(frozen=True)
class LotteryResult:
    province: str
    draw_date: str
    prizes: dict[str, list[str]]
    source_url: str
    fetched_at: datetime
    status: ResultStatus = ResultStatus.PARSED
