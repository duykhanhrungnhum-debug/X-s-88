"""Collect one public Minh Ngoc daily page and publish only validated results."""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import unicodedata

from .models import LotteryResult
from .pipeline import publish_validated_result, validate_result
from .sources.minhngoc_html import build_region_url, fetch_html, parse_html
from .supabase_store import SupabaseStore


def province_code(name: str) -> str:
    """Create a stable ASCII province key from the source display name."""
    normalized = unicodedata.normalize("NFKD", name.strip())
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return "-".join(ascii_name.split())


def collect(region: str, target_date: date) -> list[str]:
    url = build_region_url(region, target_date)
    fetched_at = datetime.now(timezone.utc)
    store = SupabaseStore.from_env()
    try:
        response = fetch_html(url)
    except Exception as exc:
        store.record_fetch(
            source_name="minhngoc",
            source_url=url,
            fetched_at=fetched_at,
            http_status=None,
            status="failed",
            error_message=str(exc),
        )
        raise

    fetch_id = store.record_fetch(
        source_name="minhngoc",
        source_url=url,
        fetched_at=fetched_at,
        http_status=response.status_code,
        status="fetched",
        content_hash=response.content_hash,
    )
    rows = parse_html(response.content, region)
    if not rows:
        raise RuntimeError(f"No {region} result rows found at {url}")

    by_province: dict[str, dict[str, list[str]]] = {}
    for row in rows:
        by_province.setdefault(row.province, {}).setdefault(row.prize_name, []).extend(row.numbers)

    published: list[str] = []
    for province, prizes in by_province.items():
        result = LotteryResult(
            province=province,
            draw_date=target_date.isoformat(),
            prizes=prizes,
            source_url=url,
            fetched_at=fetched_at,
        )
        validated = validate_result(result)
        draw_id = publish_validated_result(
            store,
            validated,
            province_code=province_code(province),
            region=region,
            source_fetch_id=fetch_id,
        )
        published.append(draw_id)
    return published


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--region", choices=["mien-bac", "mien-trung", "mien-nam"], required=True)
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args()
    ids = collect(args.region, date.fromisoformat(args.date))
    print(f"published {len(ids)} draw(s): {', '.join(ids)}")


if __name__ == "__main__":
    main()
