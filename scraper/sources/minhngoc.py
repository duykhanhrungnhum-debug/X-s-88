"""Minh Ngoc source adapter.

This module is intentionally limited to lottery-result extraction. It does not
attempt to collect advertisements, banners, tracking pixels, or unrelated page
content.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable


@dataclass(frozen=True)
class PrizeRow:
    province: str
    region: str
    prize: str
    numbers: tuple[str, ...]


PRIZE_ORDER = (
    "Giải tám",
    "Giải bảy",
    "Giải sáu",
    "Giải năm",
    "Giải tư",
    "Giải ba",
    "Giải nhì",
    "Giải nhất",
    "Giải Đặc Biệt",
)


def normalize_number(value: str) -> str:
    """Keep leading zeroes and reject non-numeric result values."""
    value = value.strip()
    if not value or not value.isdigit():
        raise ValueError(f"Invalid lottery number: {value!r}")
    return value


def build_source_url(target_date: date) -> str:
    """Build the date query URL used by the source adapter."""
    return f"https://www.minhngoc.net.vn/ket-qua-xo-so/{target_date:%d-%m-%Y}.html"


def extract_result_rows(records: Iterable[dict]) -> list[PrizeRow]:
    """Convert already-parsed source records into validated domain rows.

    HTML fetching/parsing is deliberately separate from normalization so that
    source markup changes do not leak into the domain model.
    """
    output: list[PrizeRow] = []
    for record in records:
        province = str(record["province"]).strip()
        region = str(record["region"]).strip()
        prize = str(record["prize"]).strip()
        numbers = tuple(normalize_number(str(n)) for n in record["numbers"])
        if not province or not region or prize not in PRIZE_ORDER or not numbers:
            raise ValueError("Malformed lottery result record")
        output.append(PrizeRow(province, region, prize, numbers))
    return output
