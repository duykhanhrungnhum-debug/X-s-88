import pytest

from scraper.supabase_store import SupabaseStore, normalize_supabase_url


def test_normalize_project_url():
    assert normalize_supabase_url("https://example.supabase.co") == "https://example.supabase.co"
    assert normalize_supabase_url("https://example.supabase.co/") == "https://example.supabase.co"


def test_normalize_rest_endpoint_url():
    assert normalize_supabase_url("https://example.supabase.co/rest/v1/") == "https://example.supabase.co"
    assert normalize_supabase_url("https://example.supabase.co/rest/v1") == "https://example.supabase.co"


@pytest.mark.parametrize(
    "url",
    [
        "http://example.supabase.co",
        "https://example.supabase.co/rest/v2",
        "https://example.supabase.co/functions/v1",
        "https://example.supabase.co/rest/v1?x=1",
    ],
)
def test_reject_invalid_supabase_url(url):
    with pytest.raises(RuntimeError):
        normalize_supabase_url(url)


def test_find_or_create_province_refuses_region_mismatch(monkeypatch):
    store = SupabaseStore("https://example.supabase.co", "test-secret")

    def fake_request(method, table, **kwargs):
        assert method == "GET"
        assert table == "lottery_provinces"
        return [{"id": "province-1", "name": "Đồng Nai", "region": "central"}]

    monkeypatch.setattr(store, "_request", fake_request)

    with pytest.raises(RuntimeError, match="refusing to mix regions"):
        store.find_or_create_province(code="dong-nai", name="Đồng Nai", region="south")


def test_find_or_create_province_accepts_matching_region(monkeypatch):
    store = SupabaseStore("https://example.supabase.co", "test-secret")

    monkeypatch.setattr(
        store,
        "_request",
        lambda method, table, **kwargs: [{"id": "province-1", "name": "Đồng Nai", "region": "south"}],
    )

    assert store.find_or_create_province(code="dong-nai", name="Đồng Nai", region="south") == "province-1"
