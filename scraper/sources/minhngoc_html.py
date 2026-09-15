from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date

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
    return f"https://www.minhngoc.net.vn/ket-qua-xo-so/{region}/{target_date:%d-%m-%Y}.html"


def fetch_html(url: str, *, session: requests.Session | None = None, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> FetchResponse:
    client = session or requests.Session()
    response = client.get(url, timeout=timeout, headers={"User-Agent": DEFAULT_USER_AGENT, "Accept": "text/html"})
    response.raise_for_status()
    content = response.content
    return FetchResponse(url, response.status_code, content, hashlib.sha256(content).hexdigest())


def _cell_numbers(cell: Tag) -> list[str]:
    values: list[str] = []
    for node in cell.find_all(["div", "span", "strong"], recursive=True):
        text = node.get_text(" ", strip=True)
        if text and text.isdigit():
            values.append(normalize_number(text))
    if not values:
        text = cell.get_text(" ", strip=True)
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

    # Class names and label/number pairing are based on a public Minh Ngoc
    # parser implementation. Keep this mapping isolated for easy correction.
    mapping = (
        ("giai8l", "giai8", "Giải bảy"),
        ("giai7l", "giai7", "Giải sáu"),
        ("giai6l", "giai6", "Giải năm"),
        ("giai5l", "giai5", "Giải tư"),
        ("giai4l", "giai4", "Giải ba"),
        ("giai3l", "giai3", "Giải nhì"),
        ("giai2l", "giai2", "Giải nhất"),
        ("giai1l", "giai1", "Giải Đặc Biệt"),
        ("giaidbl", "giaidb", "Giải Đặc Biệt"),
    )
    rows: list[PrizeRow] = []
    seen: set[str] = set()
    for label_class, number_class, prize_name in mapping:
        label = inner.find("td", class_=label_class)
        number_cell = inner.find("td", class_=number_class)
        if not isinstance(label, Tag) or not isinstance(number_cell, Tag):
            continue
        numbers = _cell_numbers(number_cell)
        if numbers and prize_name not in seen:
            rows.append(PrizeRow("Hà Nội", "mien-bac", prize_name, tuple(numbers)))
            seen.add(prize_name)
    return rows


def parse_mien_nam_trung(html: bytes | str, region: str) -> list[PrizeRow]:
    if region not in {"mien-nam", "mien-trung"}:
        raise ValueError(f"Unsupported region: {region}")
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("table", class_="bkqmiennam")
    if not isinstance(main, Tag):
        return []

    prize_classes = (
        ("giai8", "Giải tám"), ("giai7", "Giải bảy"), ("giai6", "Giải sáu"),
        ("giai5", "Giải năm"), ("giai4", "Giải tư"), ("giai3", "Giải ba"),
        ("giai2", "Giải nhì"), ("giai1", "Giải nhất"), ("giaidb", "Giải Đặc Biệt"),
    )
    rows: list[PrizeRow] = []
    for table in main.find_all("table", class_="rightcl"):
        province_cell = table.find("td", class_="tinh")
        if not isinstance(province_cell, Tag):
            continue
        province = province_cell.get_text(" ", strip=True)
        for prize_class, prize_name in prize_classes:
            cell = table.find("td", class_=prize_class)
            if not isinstance(cell, Tag):
                continue
            numbers = _cell_numbers(cell)
            if numbers:
                rows.append(PrizeRow(province, region, prize_name, tuple(numbers)))
    return rows


def parse_html(html: bytes | str, region: str) -> list[PrizeRow]:
    if region == "mien-bac":
        return parse_mien_bac(html)
    if region in {"mien-nam", "mien-trung"}:
        return parse_mien_nam_trung(html, region)
    raise ValueError(f"Unsupported region: {region}")
