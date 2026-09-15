from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date
from typing import Iterable

import requests
from bs4 import BeautifulSoup, Tag

from scraper.sources.minhngoc import PrizeRow, normalize_number

DEFAULT_TIMEOUT_SECONDS = 15
DEFAULT_USER_AGENT = "Xoso88/0.1 (+respectful public-results collector)"
MIN_REQUEST_INTERVAL_SECONDS = 5.0


@dataclass(frozen=True)
class FetchResponse:
    url: str
    status_code: int
    content: bytes
    content_hash: str


def build_region_url(region: str, target_date: date) -> str:
    if region not in {"mien-bac", "mien-trung", "mien-nam"}:
        raise ValueError(f"Unsupported region: {region}")
    return (
        "https://www.minhngoc.net.vn/ket-qua-xo-so/"
        f"{region}/{target_date:%d-%m-%Y}.html"
    )


def fetch_html(
    url: str,
    *,
    session: requests.Session | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> FetchResponse:
    client = session or requests.Session()
    response = client.get(
        url,
        timeout=timeout,
        headers={"User-Agent": DEFAULT_USER_AGENT, "Accept": "text/html"},
    )
    response.raise_for_status()
    content = response.content
    return FetchResponse(
        url=url,
        status_code=response.status_code,
        content=content,
        content_hash=hashlib.sha256(content).hexdigest(),
    )


def _cell_numbers(cell: Tag) -> list[str]:
    values: list[str] = []
    for node in cell.find_all(["div", "span", "strong"], recursive=True):
        text = node.get_text(" ", strip=True)
        if text and text.isdigit():
            values.append(normalize_number(text))
    if not values:
        text = cell.get_text(" ", strip=True)
        if text:
            values = [normalize_number(part) for part in text.replace("-", " ").split() if part.isdigit()]
    return values


def parse_mien_bac(html: bytes | str) -> list[PrizeRow]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="bkqmienbac")
    if not isinstance(table, Tag):
        return []
    inner = table.find("table", class_="bkqtinhmienbac")
    if not isinstance(inner, Tag):
        return []

    mapping = (
        ("giai8l", "Giải bảy"),
        ("giai7l", "Giải sáu"),
        ("giai6l", "Giải năm"),
        ("giai5l", "Giải tư"),
        ("giai4l", "Giải ba"),
        ("giai3l", "Giải nhì"),
        ("giai2l", "Giải nhất"),
        ("giai1l", "Giải Đặc Biệt"),
        ("giaidbl", "Giải Đặc Biệt"),
    )
    rows: list[PrizeRow] = []
    seen: set[str] = set()
    for label_class, prize_name in mapping:
        label = inner.find("td", class_=label_class)
        if not isinstance(label, Tag):
            continue
        row = label.find_parent("tr")
        if not isinstance(row, Tag):
            continue
        number_class = label_class[:-1] if label_class.endswith("l") else label_class
        number_cell = row.find("td", class_=number_class)
        if not isinstance(number_cell, Tag):
            continue
        numbers = _cell_numbers(number_cell)
        if numbers and prize_name not in seen:
            rows.append(PrizeRow(prize_name=prize_name, numbers=numbers))
            seen.add(prize_name)
    return rows


def parse_mien_nam_trung(html: bytes | str) -> list[PrizeRow]:
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("table", class_="bkqmiennam")
    if not isinstance(main, Tag):
        return []

    prize_classes = (
        ("giai8", "Giải tám"),
        ("giai7", "Giải bảy"),
        ("giai6", "Giải sáu"),
        ("giai5", "Giải năm"),
        ("giai4", "Giải tư"),
        ("giai3", "Giải ba"),
        ("giai2", "Giải nhì"),
        ("giai1", "Giải nhất"),
        ("giaidb", "Giải Đặc Biệt"),
    )
    rows: list[PrizeRow] = []
    for table in main.find_all("table", class_="rightcl"):
        if not isinstance(table, Tag):
            continue
        for prize_class, prize_name in prize_classes:
            cell = table.find("td", class_=prize_class)
            if not isinstance(cell, Tag):
                continue
            numbers = _cell_numbers(cell)
            if numbers:
                rows.append(PrizeRow(prize_name=prize_name, numbers=numbers))
    return rows


def parse_html(html: bytes | str, region: str) -> list[PrizeRow]:
    if region == "mien-bac":
        return parse_mien_bac(html)
    if region in {"mien-nam", "mien-trung"}:
        return parse_mien_nam_trung(html)
    raise ValueError(f"Unsupported region: {region}")
