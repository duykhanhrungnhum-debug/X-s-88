"""Trusted server-side persistence for Xoso88.

Only the collector/backend should use this module. The service-role key must
never be exposed to browser code or committed to the repository.
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from supabase import Client, create_client

from .models import LotteryResult
from .sources.minhngoc import PRIZE_ORDER


def normalize_supabase_url(url: str) -> str:
    """Return the project URL accepted by supabase-py.

    GitHub secrets in the wild are sometimes configured as the REST endpoint
    (``.../rest/v1/``) instead of the project root. Accept that documented
    deployment mistake explicitly, but reject arbitrary paths so a malformed
    secret cannot silently produce another invalid API URL.
    """
    parsed = urlsplit(url.strip())
    path = parsed.path.rstrip("/")
    if parsed.scheme != "https" or not parsed.netloc:
        raise RuntimeError("SUPABASE_URL must be an https project URL")
    if parsed.query or parsed.fragment:
        raise RuntimeError("SUPABASE_URL must not contain a query or fragment")
    if path not in ("", "/rest/v1"):
        raise RuntimeError(
            "SUPABASE_URL must be the project URL, optionally ending with /rest/v1"
        )
    return urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))


class SupabaseStore:
    """Small persistence boundary around the Xoso88 Supabase schema."""

    def __init__(self, client: Client) -> None:
        self.client = client

    @classmethod
    def from_env(cls) -> "SupabaseStore":
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required"
            )
        return cls(create_client(normalize_supabase_url(url), key))

    def record_fetch(
        self,
        *,
        source_name: str,
        source_url: str,
        fetched_at: datetime,
        http_status: int | None,
        status: str,
        content_hash: str | None = None,
        error_message: str | None = None,
    ) -> str:
        response = (
            self.client.table("source_fetches")
            .insert(
                {
                    "source_name": source_name,
                    "source_url": source_url,
                    "fetched_at": fetched_at.isoformat(),
                    "http_status": http_status,
                    "status": status,
                    "content_hash": content_hash,
                    "error_message": error_message,
                }
            )
            .execute()
        )
        if not response.data:
            raise RuntimeError("Supabase did not return the source_fetch row")
        return str(response.data[0]["id"])

    def find_or_create_province(self, *, code: str, name: str, region: str) -> str:
        existing = (
            self.client.table("lottery_provinces")
            .select("id")
            .eq("code", code)
            .maybe_single()
            .execute()
        )
        if existing.data:
            return str(existing.data["id"])

        response = (
            self.client.table("lottery_provinces")
            .insert({"code": code, "name": name, "region": region})
            .execute()
        )
        if not response.data:
            raise RuntimeError("Supabase did not return the province row")
        return str(response.data[0]["id"])

    def publish_validated_result(
        self,
        result: LotteryResult,
        *,
        province_code: str,
        region: str,
        source_fetch_id: str | None = None,
    ) -> str:
        """Persist one validated draw and its prize rows, then publish it.

        Validation must happen before this method is called. The database RLS
        prevents public clients from writing or reading unpublished data.
        """
        if result.status.value != "VALIDATED":
            raise ValueError("Only VALIDATED results may be published")

        province_id = self.find_or_create_province(
            code=province_code,
            name=result.province,
            region=region,
        )
        draw_response = (
            self.client.table("lottery_draws")
            .upsert(
                {
                    "province_id": province_id,
                    "draw_date": result.draw_date,
                    "source_url": result.source_url,
                    "fetched_at": result.fetched_at.isoformat(),
                    "validation_status": "valid",
                    "published_at": datetime.now().astimezone().isoformat(),
                },
                on_conflict="province_id,draw_date",
            )
            .execute()
        )
        if not draw_response.data:
            raise RuntimeError("Supabase did not return the draw row")

        draw_id = str(draw_response.data[0]["id"])
        rows: list[dict[str, Any]] = []
        for order, prize_name in enumerate(PRIZE_ORDER, start=1):
            numbers = result.prizes.get(prize_name, [])
            if not numbers:
                continue
            rows.append(
                {
                    "draw_id": draw_id,
                    "prize_code": f"G{order}",
                    "prize_name": prize_name,
                    "numbers": numbers,
                    "display_order": order,
                }
            )

        if not rows:
            raise ValueError("Validated result contains no prize rows")

        self.client.table("lottery_results").upsert(
            rows, on_conflict="draw_id,prize_code"
        ).execute()

        self.client.table("validation_events").insert(
            {
                "draw_id": draw_id,
                "source_fetch_id": source_fetch_id,
                "status": "valid",
                "reason": "validated result published by trusted backend",
            }
        ).execute()
        return draw_id
