from datetime import date

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
        url="https://www.minhngoc.net.vn/ket-qua-xo-so/15-09-2026.html",
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
    monkeypatch.setattr(collect_live, "parse_html", lambda content, region: rows)
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


def test_all_source_regions_have_database_enum_mapping():
    assert collect_live.SOURCE_TO_DB_REGION == {
        "mien-bac": "north",
        "mien-trung": "central",
        "mien-nam": "south",
    }
