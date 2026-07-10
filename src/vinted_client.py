"""Vinted API client with session management, retries and cloud-friendly fallbacks."""

from __future__ import annotations

import logging
import time
from typing import Any

from curl_cffi import requests

from .config import AppConfig

logger = logging.getLogger(__name__)

IMPERSONATE_PROFILES = ("chrome120", "chrome110", "chrome131", "safari15_5")


class VintedClient:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.last_error: str | None = None
        self._impersonate_idx = 0
        self.session = self._new_session()
        self._session_initialized = False
        self._last_request_at = 0.0

    def _new_session(self):
        profile = IMPERSONATE_PROFILES[self._impersonate_idx % len(IMPERSONATE_PROFILES)]
        try:
            return requests.Session(impersonate=profile)
        except Exception:
            return requests.Session(impersonate="chrome120")

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": f"{self.config.base_url}/",
            "Origin": self.config.base_url,
            "X-Requested-With": "XMLHttpRequest",
        }

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        delay = self.config.request_delay_seconds
        if elapsed < delay:
            time.sleep(delay - elapsed)

    def _ensure_session(self) -> None:
        if self._session_initialized:
            return
        self._throttle()
        base = self.config.base_url
        for path in ("/", "/catalog"):
            try:
                resp = self.session.get(
                    base + path, timeout=45, headers=self._headers(),
                )
                if resp.status_code < 500:
                    break
            except Exception as exc:
                logger.warning("Session init %s failed: %s", path, exc)
        self._session_initialized = True
        self._last_request_at = time.monotonic()
        logger.info("Vinted session ready (%d cookies)", len(self.session.cookies))

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self._ensure_session()
        url = self.config.base_url + path
        last_exc: Exception | None = None

        for attempt in range(4):
            self._throttle()
            try:
                resp = self.session.get(
                    url, params=params, timeout=45, headers=self._headers(),
                )
                self._last_request_at = time.monotonic()

                if resp.status_code in (401, 403):
                    logger.warning("Vinted %s on attempt %d, resetting session", resp.status_code, attempt + 1)
                    self.reset_session(rotate=True)
                    continue

                if resp.status_code >= 400:
                    self.last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                    resp.raise_for_status()

                self.last_error = None
                return resp.json()
            except Exception as exc:
                last_exc = exc
                self.last_error = f"{type(exc).__name__}: {exc}"
                logger.warning("Vinted request failed (attempt %d): %s", attempt + 1, self.last_error)
                self.reset_session(rotate=True)
                time.sleep(1.5 * (attempt + 1))

        raise last_exc or RuntimeError(self.last_error or "Vinted request failed")

    def search_catalog(
        self,
        search_text: str,
        *,
        per_page: int | None = None,
        order: str = "newest_first",
        catalog_ids: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "search_text": search_text,
            "per_page": per_page or self.config.listings_per_search,
            "order": order,
        }
        if catalog_ids:
            params["catalog_ids"] = catalog_ids

        data = self._get("/api/v2/catalog/items", params=params)
        items = data.get("items", [])
        if not items and data.get("code"):
            self.last_error = str(data.get("message", data.get("code")))
        return items

    def reset_session(self, rotate: bool = False) -> None:
        if rotate:
            self._impersonate_idx += 1
        self.session = self._new_session()
        self._session_initialized = False

    def test_connection(self) -> dict[str, Any]:
        """Diagnostic — teste une recherche simple."""
        try:
            items = self.search_catalog("Nike", per_page=5)
            return {
                "ok": True,
                "items_count": len(items),
                "sample_title": items[0].get("title") if items else None,
                "error": None,
            }
        except Exception as exc:
            return {"ok": False, "items_count": 0, "error": str(exc), "last_error": self.last_error}
