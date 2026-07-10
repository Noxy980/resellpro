"""Vinted account management — profile, listings, sales."""

from __future__ import annotations

import logging
from typing import Any

from src.vinted_client import VintedClient

logger = logging.getLogger(__name__)


class VintedAccountService:
    def __init__(self, client: VintedClient) -> None:
        self.client = client

    def get_profile(self) -> dict[str, Any]:
        try:
            data = self.client._get("/api/v2/users/current")
            user = data.get("user", data)
            return {
                "id": user.get("id"),
                "login": user.get("login", ""),
                "photo": user.get("photo", {}).get("url") if user.get("photo") else None,
                "item_count": user.get("item_count", 0),
                "feedback_count": user.get("feedback_count", 0),
                "positive_feedback": user.get("positive_feedback_count", 0),
                "is_connected": True,
            }
        except Exception as exc:
            logger.warning("Profile fetch failed: %s", exc)
            return {"is_connected": False, "error": str(exc)}

    def get_my_listings(self, user_id: int, per_page: int = 48) -> list[dict[str, Any]]:
        try:
            data = self.client._get(
                f"/api/v2/wardrobe/{user_id}/items",
                params={"per_page": per_page, "order": "newest_first"},
            )
            items = data.get("items", [])
            return [self._format_listing(i) for i in items]
        except Exception:
            try:
                data = self.client._get("/api/v2/catalog/items", params={
                    "user_id": user_id, "per_page": per_page,
                })
                return [self._format_listing(i) for i in data.get("items", [])]
            except Exception as exc:
                logger.error("Listings fetch failed: %s", exc)
                return []

    def _format_listing(self, item: dict) -> dict:
        price = item.get("price") or {}
        return {
            "id": item.get("id"),
            "title": item.get("title", ""),
            "brand": item.get("brand_title", ""),
            "price": float(price.get("amount", 0)),
            "currency": price.get("currency_code", "EUR"),
            "status": item.get("status", ""),
            "size": item.get("size_title", ""),
            "url": item.get("url", ""),
            "image_url": (item.get("photo") or {}).get("url"),
            "favourite_count": item.get("favourite_count", 0),
            "view_count": item.get("view_count", 0),
            "is_visible": item.get("is_visible", True),
        }

    def prepare_listing_url(self, draft: dict) -> str:
        """Open Vinted sell page — full API publish requires authenticated seller session."""
        base = self.client.config.base_url
        return f"{base}/items/new"
