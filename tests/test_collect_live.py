from datetime import date

import pytest

from scraper import collect_live
from scraper.sources.minhngoc import PrizeRow
from scraper.sources.minhngoc_html import FetchResponse


class FakeStore:
    def __init__(self):
        self.fetch_calls = []
        self.publish_calls = []

    def record_fetch(self, **kwargs):
        self.fetch_calls.append(kwargs)
        return "fetch-1"


def test_collect_maps_source_region_to_database_enum(monkeypatch):
    store = FakeStore()
    response = FetchResponse(
        url="https://www.minhngoc.net.vn/ket-qua-xo-so/mien-nam/15-09-2026.html",
        status_code=200,
        content=b"fixture",
        content_hash="hash",
    )
    rows = [
        PrizeRow("Tây Ninh", "mien-nam", "Giải tám", ("09",)),
        PrizeRow("Tây Ninh", "mien-nam", "Giải Đặc Biệt", ("012345",)),
    ]

    monkeypatch.setattr(collect_live.SupabaseStore, "from_env", lambda: store)
    monkeypatch.setattr(collect_live, "fetch_html", lambda url: response)
    monkeypatch.setattr(collect_live, "extract_region_result_date", lambda content, region: date(2026, 9, 15))
    monkeypatch.setattr(collect_live, "parse_html", lambda content, region, target_date=None: rows)
    monkeypatch.setattr(collect_live, "validate_result", lambda result: result)
    monkeypatch.setattr(
        collect_live,
        "publish_validated_result",
        lambda store, result, **kwargs: store.publish_calls.append((result, kwargs)) or "draw-1",
    )

    published = collect_live.collect("mien-nam", date(2026, 9, 15))

    assert published == ["draw-1"]
    assert len(store.fetch_calls) == 1
    result, kwargs = store.publish_calls[0]
    assert result.province == "Tây Ninh"
    assert result.prizes == {"Giải tám": ["09"], "Giải Đặc Biệt": ["012345"]}
    assert kwargs["region"] == "south"
    assert kwargs["source_fetch_id"] == "fetch-1"


def test_collect_refuses_mismatched_source_date(monkeypatch):
    store = FakeStore()
    response = FetchResponse(
        url="https://www.minhngoc.net.vn/ket-qua-xo-so/mien-nam/17-09-2026.html",
        status_code=200,
        content=b"fixture",
        content_hash="hash",
    )

    monkeypatch.setattr(collect_live.SupabaseStore, "from_env", lambda: store)
    monkeypatch.setattr(collect_live, "fetch_html", lambda url: response)
    monkeypatch.setattr(collect_live, "extract_region_result_date", lambda content, region: date(2026, 9, 16))
    monkeypatch.setattr(collect_live, "parse_html", lambda content, region, target_date=None: pytest.fail("parser must not run"))

    with pytest.raises(RuntimeError, match="refusing to publish mismatched data"):
        collect_live.collect("mien-nam", date(2026, 9, 17))

    assert len(store.publish_calls) == 0


def test_all_source_regions_have_database_enum_mapping():
    assert collect_live.SOURCE_TO_DB_REGION == {
        "mien-bac": "north",
        "mien-trung": "central",
        "mien-nam": "south",
    }


def test_province_code_preserves_vietnamese_d_as_ascii_d():
    assert collect_live.province_code("Đà Nẵng") == "da-nang"
    assert collect_live.province_code("Đồng Nai") == "dong-nai"
    assert collect_live.province_code("Đắk Nông") == "dak-nong"


def test_province_code_normalizes_punctuation():
    assert collect_live.province_code("TP. HCM") == "tp-hcm"
