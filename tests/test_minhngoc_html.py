from datetime import date

import pytest

from scraper.sources.minhngoc_html import (
    HostRateLimiter,
    build_region_url,
    extract_region_result_date,
    parse_html,
)


MB_FIXTURE = """
<div>KẾT QUẢ XỔ SỐ Miền Bắc - 16/09/2026</div>
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
<div>KẾT QUẢ XỔ SỐ Miền Nam - 16/09/2026</div>
<table class="bkqmiennam"><tr><td><table class="rightcl">
<td class="tinh">Tây Ninh</td>
<td class="giai8"><div>09</div></td>
<td class="giai7"><div>123</div></td>
<td class="giaidb"><div>012345</div></td>
</table></td></tr></table>
"""

MT_FIXTURE = """
<div>KẾT QUẢ XỔ SỐ Miền Trung - 16/09/2026</div>
<section><table class="some-regional-wrapper"><tr><td><table class="rightcl">
<td class="tinh">Đà Nẵng</td>
<td class="giai8"><div>23</div></td>
<td class="giai1"><div>90069</div></td>
<td class="giaidb"><div>173506</div></td>
</table></td></tr></table></section>
"""


def test_build_region_url_uses_region_specific_daily_pages():
    assert build_region_url("mien-bac", date(2026, 9, 15)) == (
        "https://www.minhngoc.net.vn/ket-qua-xo-so/mien-bac/15-09-2026.html"
    )
    assert build_region_url("mien-trung", date(2026, 9, 15)) == (
        "https://www.minhngoc.net.vn/ket-qua-xo-so/mien-trung/15-09-2026.html"
    )
    assert build_region_url("mien-nam", date(2026, 9, 15)) == (
        "https://www.minhngoc.net.vn/ket-qua-xo-so/mien-nam/15-09-2026.html"
    )


def test_extract_region_result_date():
    assert extract_region_result_date(MB_FIXTURE, "mien-bac") == date(2026, 9, 16)
    assert extract_region_result_date(MT_FIXTURE, "mien-trung") == date(2026, 9, 16)
    assert extract_region_result_date(MN_FIXTURE, "mien-nam") == date(2026, 9, 16)
    assert extract_region_result_date("<html>no results</html>", "mien-nam") is None


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


def test_parse_mien_trung_uses_province_tables():
    rows = parse_html(MT_FIXTURE, "mien-trung")
    assert any(row.province == "Đà Nẵng" and row.prize == "Giải tám" and row.numbers == ("23",) for row in rows)
    assert any(row.province == "Đà Nẵng" and row.prize == "Giải nhất" and row.numbers == ("90069",) for row in rows)



def test_mien_nam_ignores_sidebar_province_tables_outside_primary_result_block():
    html = """
    <div>KẾT QUẢ XỔ SỐ Miền Nam - 20/09/2026</div>
    <table class="bkqmiennam"><tr><td>
      <table class="rightcl">
        <td class="tinh">Tiền Giang</td>
        <td class="giai8"><div>08</div></td>
        <td class="giaidb"><div>248087</div></td>
      </table>
      <table class="rightcl">
        <td class="tinh">Kiên Giang</td>
        <td class="giai8"><div>35</div></td>
        <td class="giaidb"><div>237748</div></td>
      </table>
      <table class="rightcl">
        <td class="tinh">Đà Lạt</td>
        <td class="giai8"><div>44</div></td>
        <td class="giaidb"><div>722323</div></td>
      </table>
    </td></tr></table>
    <aside>
      <table class="rightcl">
        <td class="tinh">Tây Ninh</td>
        <td class="giai8"><div>77</div></td>
        <td class="giaidb"><div>024183</div></td>
      </table>
    </aside>
    """
    rows = parse_html(html, "mien-nam")
    provinces = {row.province for row in rows}
    assert provinces == {"Tiền Giang", "Kiên Giang", "Đà Lạt"}
    assert "Tây Ninh" not in provinces


def test_mien_trung_ignores_sidebar_province_tables_when_primary_wrapper_exists():
    html = """
    <div>KẾT QUẢ XỔ SỐ Miền Trung - 20/09/2026</div>
    <table class="bkqmientrung"><tr><td>
      <table class="rightcl">
        <td class="tinh">Kon Tum</td>
        <td class="giai8"><div>38</div></td>
        <td class="giaidb"><div>595460</div></td>
      </table>
      <table class="rightcl">
        <td class="tinh">Huế</td>
        <td class="giai8"><div>05</div></td>
        <td class="giaidb"><div>172613</div></td>
      </table>
      <table class="rightcl">
        <td class="tinh">Khánh Hòa</td>
        <td class="giai8"><div>02</div></td>
        <td class="giaidb"><div>921848</div></td>
      </table>
    </td></tr></table>
    <aside>
      <table class="rightcl">
        <td class="tinh">Đà Nẵng</td>
        <td class="giai8"><div>99</div></td>
        <td class="giaidb"><div>999999</div></td>
      </table>
    </aside>
    """
    rows = parse_html(html, "mien-trung")
    provinces = {row.province for row in rows}
    assert provinces == {"Kon Tum", "Huế", "Khánh Hòa"}
    assert "Đà Nẵng" not in provinces


def test_schedule_filter_keeps_only_sunday_mien_nam_provinces():
    html = """
    <div>KẾT QUẢ XỔ SỐ Miền Nam - 20/09/2026</div>
    <table class="bkqmiennam"><tr><td>
      <table class="rightcl"><td class="tinh">Tiền Giang</td><td class="giai8"><div>08</div></td></table>
      <table class="rightcl"><td class="tinh">Kiên Giang</td><td class="giai8"><div>35</div></td></table>
      <table class="rightcl"><td class="tinh">Đà Lạt</td><td class="giai8"><div>44</div></td></table>
      <table class="rightcl"><td class="tinh">Tây Ninh</td><td class="giai8"><div>77</div></td></table>
    </td></tr></table>
    """
    rows = parse_html(html, "mien-nam", date(2026, 9, 20))
    assert {row.province for row in rows} == {"Tiền Giang", "Kiên Giang", "Đà Lạt"}


def test_schedule_filter_keeps_current_sunday_mien_trung_provinces():
    html = """
    <div>KẾT QUẢ XỔ SỐ Miền Trung - 20/09/2026</div>
    <table class="bkqmiennam"><tr><td>
      <table class="rightcl"><td class="tinh">Kon Tum</td><td class="giai8"><div>38</div></td></table>
      <table class="rightcl"><td class="tinh">Huế</td><td class="giai8"><div>05</div></td></table>
      <table class="rightcl"><td class="tinh">Khánh Hòa</td><td class="giai8"><div>02</div></td></table>
      <table class="rightcl"><td class="tinh">Đà Nẵng</td><td class="giai8"><div>59</div></td></table>
    </td></tr></table>
    """
    rows = parse_html(html, "mien-trung", date(2026, 9, 20))
    assert {row.province for row in rows} == {"Kon Tum", "Huế", "Khánh Hòa"}

def test_rate_limiter_enforces_five_seconds_per_host():
    clock = [100.0]
    sleeps: list[float] = []

    def monotonic() -> float:
        return clock[0]

    def sleeper(seconds: float) -> None:
        sleeps.append(seconds)
        clock[0] += seconds

    limiter = HostRateLimiter(interval_seconds=5.0, monotonic=monotonic, sleeper=sleeper)
    url = "https://www.minhngoc.net.vn/ket-qua-xo-so/mien-nam/15-09-2026.html"
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
