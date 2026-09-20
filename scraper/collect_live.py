"""Collect one public Minh Ngoc daily page and publish only validated results."""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo
import re
import unicodedata

from .models import LotteryResult
from .pipeline import publish_validated_result, validate_result
from .sources.minhngoc_html import (
    build_region_url,
    extract_region_result_date,
    fetch_html,
    parse_html,
)
from .supabase_store import SupabaseStore


SOURCE_TO_DB_REGION = {
    "mien-bac": "north",
    "mien-trung": "central",
    "mien-nam": "south",
}


class SourceDateMismatchError(RuntimeError):
    """The requested day's source page exists but is not published yet."""


def province_code(name: str) -> str:
    """Create a stable lowercase ASCII slug from the source display name."""
    source = name.strip().replace("Đ", "D").replace("đ", "d")
    normalized = unicodedata.normalize("NFKD", source)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_name).strip("-")


def collect(region: str, target_date: date) -> list[str]:
    if region not in SOURCE_TO_DB_REGION:
        raise ValueError(f"Unsupported collector region: {region}")

    db_region = SOURCE_TO_DB_REGION[region]
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

    actual_date = extract_region_result_date(response.content, region)
    if actual_date != target_date:
        raise SourceDateMismatchError(
            f"Minh Ngoc returned {region} results for {actual_date.isoformat() if actual_date else 'an unknown date'}, "
            f"but collector requested {target_date.isoformat()}; refusing to publish mismatched data"
        )

    rows = parse_html(response.content, region, target_date)
    if not rows:
        raise RuntimeError(f"No {region} result rows found for {target_date.isoformat()} at {url}")

    by_province: dict[str, dict[str, list[str]]] = {}
    for row in rows:
        by_province.setdefault(row.province, {}).setdefault(row.prize, []).extend(row.numbers)

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
            region=db_region,
            source_fetch_id=fetch_id,
        )
        published.append(draw_id)
    return published


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--region", choices=["mien-bac", "mien-trung", "mien-nam"], required=True)
    parser.add_argument(
        "--date",
        help="Exact source date to collect. Omit for scheduled mode, which waits for today's published results.",
    )
    args = parser.parse_args()
    target_date = (
        date.fromisoformat(args.date)
        if args.date
        else datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date()
    )

    try:
        ids = collect(args.region, target_date)
    except SourceDateMismatchError as exc:
        if not args.date:
            print(f"No {args.region} results published for {target_date.isoformat()} yet; waiting for the next scheduled run.")
            return
        raise exc

    print(f"published {len(ids)} draw(s): {', '.join(ids)}")


if __name__ == "__main__":
    main()
