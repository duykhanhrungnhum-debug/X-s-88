"""Trusted server-side persistence for Xoso88.

Only the collector/backend should use this module. The secret key must
never be exposed to browser code or committed to the repository.
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import requests

from .models import LotteryResult
from .sources.minhngoc import PRIZE_ORDER


class SupabaseStore:
    """Small persistence boundary around the Xoso88 Supabase schema."""

    def __init__(self, base_url: str, key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.key = key
        self.session = requests.Session()
        # New sb_secret_* keys are opaque API keys. Send them as the API key
        # itself and do not manufacture a JWT Authorization header.
        self.session.headers.update({
            "apikey": key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

    @staticmethod
    def normalize_supabase_url(url: str) -> str:
        """Return the project URL accepted by the REST API."""
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

    @classmethod
    def from_env(cls) -> "SupabaseStore":
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required"
            )
        return cls(cls.normalize_supabase_url(url), key)

    def _request(
        self,
        method: str,
        table: str,
        *,
        params: dict[str, str] | None = None,
        json: Any = None,
        prefer: str | None = None,
    ) -> list[dict[str, Any]]:
        headers = {}
        if prefer:
            headers["Prefer"] = prefer
        response = self.session.request(
            method,
            f"{self.base_url}/rest/v1/{table}",
            params=params,
            json=json,
            headers=headers,
            timeout=15,
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f"Supabase REST {method} {table} failed with HTTP {response.status_code}: "
                f"{response.text[:500]}"
            )
        if not response.content:
            return []
        data = response.json()
        return data if isinstance(data, list) else [data]

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
        rows = self._request(
            "POST",
            "source_fetches",
            json={
                "source_name": source_name,
                "source_url": source_url,
                "fetched_at": fetched_at.isoformat(),
                "http_status": http_status,
                "status": status,
                "content_hash": content_hash,
                "error_message": error_message,
            },
            prefer="return=representation",
        )
        if not rows:
            raise RuntimeError("Supabase did not return the source_fetch row")
        return str(rows[0]["id"])

    def find_or_create_province(self, *, code: str, name: str, region: str) -> str:
        existing = self._request(
            "GET",
            "lottery_provinces",
            params={"select": "id,name,region", "code": f"eq.{code}", "limit": "1"},
        )
        if existing:
            existing_region = existing[0].get("region")
            if existing_region != region:
                raise RuntimeError(
                    f"Province code {code!r} is already mapped to region {existing_region!r}, "
                    f"but collector requested {region!r}; refusing to mix regions"
                )
            return str(existing[0]["id"])

        rows = self._request(
            "POST",
            "lottery_provinces",
            json={"code": code, "name": name, "region": region},
            prefer="return=representation",
        )
        if not rows:
            raise RuntimeError("Supabase did not return the province row")
        return str(rows[0]["id"])

    def publish_validated_result(
        self,
        result: LotteryResult,
        *,
        province_code: str,
        region: str,
        source_fetch_id: str | None = None,
    ) -> str:
        """Persist one validated draw and its prize rows, then publish it."""
        if result.status.value != "VALIDATED":
            raise ValueError("Only VALIDATED results may be published")

        province_id = self.find_or_create_province(
            code=province_code,
            name=result.province,
            region=region,
        )
        draw_rows = self._request(
            "POST",
            "lottery_draws",
            params={"on_conflict": "province_id,draw_date"},
            json={
                "province_id": province_id,
                "draw_date": result.draw_date,
                "source_url": result.source_url,
                "fetched_at": result.fetched_at.isoformat(),
                "validation_status": "valid",
                "published_at": datetime.now().astimezone().isoformat(),
            },
            prefer="resolution=merge-duplicates,return=representation",
        )
        if not draw_rows:
            raise RuntimeError("Supabase did not return the draw row")

        draw_id = str(draw_rows[0]["id"])
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

        self._request(
            "POST",
            "lottery_results",
            params={"on_conflict": "draw_id,prize_code"},
            json=rows,
            prefer="resolution=merge-duplicates,return=minimal",
        )
        self._request(
            "POST",
            "validation_events",
            json={
                "draw_id": draw_id,
                "source_fetch_id": source_fetch_id,
                "status": "valid",
                "reason": "validated result published by trusted backend",
            },
            prefer="return=minimal",
        )
        return draw_id
