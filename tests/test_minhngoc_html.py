from datetime import date

import pytest

from scraper.sources.minhngoc_html import HostRateLimiter, build_region_url, parse_html


MB_FIXTURE = """
<table class="bkqmienbac"><tr><td><table class="bkqtinhmienbac">
<tr><td class="giai1l">Giải nhất</td><td class="giai1"><div>12345</div></td></tr>
<tr><td class="giai2l">Giải nhì</td><td class="giai2"><div>01234</div><div>56789</div></td></tr>
<tr><td class="giai3l">Giải ba</td><td class="giai3"><div>12345</div><div>23456</div></td></tr>
<tr><td class="giai4l">Giải tư</td><td class="giai4"><div>1234</div></td></tr>
<tr><td class="giai5l">Giải năm</td><td class="giai5"><div>1234</div></td></tr>
<tr><td class="giai6l">Giải sáu</td><td class="giai6"><div>123</div></td></tr>
<tr><td class="giai7l">Giải bảy</td><td class="giai7"><div>12</div></td></tr>
<tr><td class="giai8l">Giải tám</td><td class="giai8"><div>99</div></td></tr>
<tr><td class="giaidbl">Giải ĐB</td><td class="giaidb"><div>12345</div></td></tr>
</table></td></tr></table>
"""

MN_FIXTURE = """
<table class="bkqmiennam"><tr><td><table class="rightcl">
<td class="tinh">Tây Ninh</td>
<td class="giai8"><div>09</div></td>
<td class="giai7"><div>123</div></td>
<td class="giaidb"><div>012345</div></td>
</table></td></tr></table>
"""


def test_build_region_url_uses_verified_daily_page():
    assert build_region_url("mien-nam", date(2026, 9, 15)) == (
        "https://www.minhngoc.net.vn/ket-qua-xo-so/15-09-2026.html"
    )


def test_parse_mien_bac_preserves_leading_zeroes():
    rows = parse_html(MB_FIXTURE, "mien-bac")
    assert any(row.prize == "Giải nhì" and row.numbers == ("01234", "56789") for row in rows)
    assert any(row.prize == "Giải tám" and row.numbers == ("99",) for row in rows)
    assert any(row.prize == "Giải Đặc Biệt" and row.numbers == ("12345",) for row in rows)


def test_parse_mien_bac_maps_all_prizes():
    rows = parse_html(MB_FIXTURE, "mien-bac")
    assert [row.prize for row in rows] == [
        "Giải tám", "Giải bảy", "Giải sáu", "Giải năm", "Giải tư",
        "Giải ba", "Giải nhì", "Giải nhất", "Giải Đặc Biệt",
    ]


def test_parse_mien_nam_extracts_province_and_numbers():
    rows = parse_html(MN_FIXTURE, "mien-nam")
    assert any(row.province == "Tây Ninh" and row.prize == "Giải tám" and row.numbers == ("09",) for row in rows)
    assert any(row.prize == "Giải Đặc Biệt" and row.numbers == ("012345",) for row in rows)


def test_rate_limiter_enforces_five_seconds_per_host():
    clock = [100.0]
    sleeps: list[float] = []

    def monotonic() -> float:
        return clock[0]

    def sleeper(seconds: float) -> None:
        sleeps.append(seconds)
        clock[0] += seconds

    limiter = HostRateLimiter(interval_seconds=5.0, monotonic=monotonic, sleeper=sleeper)
    url = "https://www.minhngoc.net.vn/ket-qua-xo-so/15-09-2026.html"
    limiter.wait(url)
    clock[0] += 1.0
    limiter.wait(url)
    assert sleeps == [4.0]


def test_rate_limiter_is_independent_per_host():
    clock = [100.0]
    sleeps: list[float] = []

    def monotonic() -> float:
        return clock[0]

    def sleeper(seconds: float) -> None:
        sleeps.append(seconds)
        clock[0] += seconds

    limiter = HostRateLimiter(interval_seconds=5.0, monotonic=monotonic, sleeper=sleeper)
    limiter.wait("https://www.minhngoc.net.vn/a")
    limiter.wait("https://example.com/b")
    assert sleeps == []


def test_unknown_region_rejected():
    with pytest.raises(ValueError):
        parse_html("<html></html>", "unknown")
