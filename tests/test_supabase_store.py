import pytest

from scraper.supabase_store import normalize_supabase_url


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
