"""Vinted API client with session management and rate limiting."""

from __future__ import annotations

import logging
import time
from typing import Any

from curl_cffi import requests

from .config import AppConfig

logger = logging.getLogger(__name__)


class VintedClient:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.session = requests.Session(impersonate="chrome131")
        self._session_initialized = False
        self._last_request_at = 0.0

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        delay = self.config.request_delay_seconds
        if elapsed < delay:
            time.sleep(delay - elapsed)

    def _ensure_session(self) -> None:
        if self._session_initialized:
            return
        self._throttle()
        resp = self.session.get(self.config.base_url + "/", timeout=30)
        resp.raise_for_status()
        self._session_initialized = True
        self._last_request_at = time.monotonic()
        logger.debug("Vinted session initialized (%d cookies)", len(self.session.cookies))

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self._ensure_session()
        self._throttle()
        url = self.config.base_url + path
        resp = self.session.get(url, params=params, timeout=30)
        self._last_request_at = time.monotonic()

        if resp.status_code == 401:
            logger.warning("Session expired, re-initializing...")
            self._session_initialized = False
            self._ensure_session()
            self._throttle()
            resp = self.session.get(url, params=params, timeout=30)
            self._last_request_at = time.monotonic()

        resp.raise_for_status()
        return resp.json()

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
        return data.get("items", [])

    def reset_session(self) -> None:
        self.session = requests.Session(impersonate="chrome131")
        self._session_initialized = False
