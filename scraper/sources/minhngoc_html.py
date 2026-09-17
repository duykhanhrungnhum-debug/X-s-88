from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from threading import Lock
from typing import Callable
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, Tag

from scraper.sources.minhngoc import PrizeRow, normalize_number

DEFAULT_TIMEOUT_SECONDS = 15
DEFAULT_USER_AGENT = "Xoso88/0.1 (+respectful public-results collector)"
MIN_REQUEST_INTERVAL_SECONDS = 5.0
SOURCE_REGION_NAMES = {
    "mien-bac": "Bắc",
    "mien-trung": "Trung",
    "mien-nam": "Nam",
}


@dataclass(frozen=True)
class FetchResponse:
    url: str
    status_code: int
    content: bytes
    content_hash: str


@dataclass
class HostRateLimiter:
    """Serialize requests per host and enforce a minimum interval."""

    interval_seconds: float = MIN_REQUEST_INTERVAL_SECONDS
    monotonic: Callable[[], float] = time.monotonic
    sleeper: Callable[[float], None] = time.sleep
    _last_request_at: dict[str, float] = field(default_factory=dict, init=False)
    _lock: Lock = field(default_factory=Lock, init=False)

    def wait(self, url: str) -> None:
        host = urlparse(url).netloc.lower()
        with self._lock:
            now = self.monotonic()
            last = self._last_request_at.get(host)
            if last is not None:
                remaining = self.interval_seconds - (now - last)
                if remaining > 0:
                    self.sleeper(remaining)
                    now = self.monotonic()
            self._last_request_at[host] = now


def build_region_url(region: str, target_date: date) -> str:
    """Build the verified region-specific Minh Ngoc daily result URL."""
    if region not in SOURCE_REGION_NAMES:
        raise ValueError(f"Unsupported region: {region}")
    return (
        f"https://www.minhngoc.net.vn/ket-qua-xo-so/{region}/{target_date:%d-%m-%Y}.html"
    )


def fetch_html(
    url: str,
    *,
    session: requests.Session | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    rate_limiter: HostRateLimiter | None = None,
) -> FetchResponse:
    limiter = rate_limiter or HostRateLimiter()
    limiter.wait(url)
    client = session or requests.Session()
    response = client.get(
        url,
        timeout=timeout,
        headers={"User-Agent": DEFAULT_USER_AGENT, "Accept": "text/html"},
    )
    response.raise_for_status()
    content = response.content
    return FetchResponse(url, response.status_code, content, hashlib.sha256(content).hexdigest())


def extract_region_result_date(html: bytes | str, region: str) -> date | None:
    """Extract the date attached to the requested region result section."""
    if region not in SOURCE_REGION_NAMES:
        raise ValueError(f"Unsupported region: {region}")
    soup = BeautifulSoup(html, "html.parser")
    text = " ".join(soup.get_text(" ", strip=True).split())
    region_name = SOURCE_REGION_NAMES[region]
    pattern = re.compile(
        rf"KẾT QUẢ\s+XỔ\s+SỐ\s+Miền\s+{re.escape(region_name)}\s*-\s*(\d{{2}}/\d{{2}}/\d{{4}})",
        re.IGNORECASE,
    )
    match = pattern.search(text)
    if not match:
        return None
    return datetime.strptime(match.group(1), "%d/%m/%Y").date()


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

    mapping = (
        ("giai8l", "giai8", "Giải tám"),
        ("giai7l", "giai7", "Giải bảy"),
        ("giai6l", "giai6", "Giải sáu"),
        ("giai5l", "giai5", "Giải năm"),
        ("giai4l", "giai4", "Giải tư"),
        ("giai3l", "giai3", "Giải ba"),
        ("giai2l", "giai2", "Giải nhì"),
        ("giai1l", "giai1", "Giải nhất"),
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


def _result_tables(soup: BeautifulSoup) -> list[Tag]:
    """Find province result tables without assuming a region wrapper class."""
    prize_classes = (
        "giai8", "giai7", "giai6", "giai5", "giai4",
        "giai3", "giai2", "giai1", "giaidb",
    )
    tables: list[Tag] = []
    for table in soup.find_all("table"):
        if not isinstance(table, Tag):
            continue
        province_cell = table.find("td", class_="tinh")
        if not isinstance(province_cell, Tag):
            continue
        if any(isinstance(table.find("td", class_=cls), Tag) for cls in prize_classes):
            tables.append(table)
    return tables


def parse_mien_nam_trung(html: bytes | str, region: str) -> list[PrizeRow]:
    if region not in {"mien-nam", "mien-trung"}:
        raise ValueError(f"Unsupported region: {region}")
    soup = BeautifulSoup(html, "html.parser")
    prize_classes = (
        ("giai8", "Giải tám"), ("giai7", "Giải bảy"), ("giai6", "Giải sáu"),
        ("giai5", "Giải năm"), ("giai4", "Giải tư"), ("giai3", "Giải ba"),
        ("giai2", "Giải nhì"), ("giai1", "Giải nhất"), ("giaidb", "Giải Đặc Biệt"),
    )
    rows: list[PrizeRow] = []
    for table in _result_tables(soup):
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
