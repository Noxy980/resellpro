"""Vinted account management — profile, listings, sales, cookies."""

from __future__ import annotations

import json
import logging
from typing import Any
from urllib.parse import quote

from src.vinted_client import VintedClient

logger = logging.getLogger(__name__)


def parse_cookies(raw: str) -> dict[str, str]:
    """Parse cookie string (header format or JSON array from browser extension)."""
    raw = (raw or "").strip()
    if not raw:
        return {}
    if raw.startswith("["):
        try:
            arr = json.loads(raw)
            return {
                str(c["name"]): str(c["value"])
                for c in arr
                if isinstance(c, dict) and c.get("name") and c.get("value") is not None
            }
        except json.JSONDecodeError:
            pass
    result: dict[str, str] = {}
    for part in raw.split(";"):
        part = part.strip()
        if "=" in part:
            key, val = part.split("=", 1)
            result[key.strip()] = val.strip()
    return result


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
                data = self.client._get(
                    "/api/v2/catalog/items",
                    params={"user_id": user_id, "per_page": per_page},
                )
                return [self._format_listing(i) for i in data.get("items", [])]
            except Exception as exc:
                logger.error("Listings fetch failed: %s", exc)
                return []

    def get_sales(self, user_id: int) -> list[dict[str, Any]]:
        """Fetch completed sales from Vinted (requires authenticated session cookies)."""
        attempts: list[tuple[str, dict[str, Any]]] = [
            ("/api/v2/orders", {"status": "completed", "per_page": 48}),
            ("/api/v2/wallet/orders", {"per_page": 48}),
            (f"/api/v2/wardrobe/{user_id}/items", {"filter": "sold", "per_page": 48}),
            (f"/api/v2/users/{user_id}/items", {"filter": "sold", "per_page": 48}),
        ]
        for path, params in attempts:
            try:
                data = self.client._get(path, params=params)
                items = data.get("items") or data.get("orders") or []
                if items:
                    return [self._format_sale(i) for i in items]
            except Exception as exc:
                logger.debug("Sales endpoint %s failed: %s", path, exc)
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

    def _format_sale(self, item: dict) -> dict:
        price = item.get("price") or item.get("total_price") or {}
        amount = price.get("amount", price) if isinstance(price, dict) else price
        return {
            "id": item.get("id"),
            "title": item.get("title", item.get("item_title", "")),
            "brand": item.get("brand_title", ""),
            "price": float(amount or 0),
            "status": item.get("status", "sold"),
            "sold_at": item.get("sold_at") or item.get("created_at", ""),
            "url": item.get("url", ""),
            "image_url": (item.get("photo") or {}).get("url"),
            "buyer": (item.get("buyer") or {}).get("login", ""),
        }

    def prepare_publish_url(self, draft: dict) -> str:
        """Open Vinted sell page — full API publish needs seller cookies + photos."""
        base = f"{self.client.config.base_url}/items/new"
        title = str(draft.get("title", ""))[:80]
        desc = str(draft.get("description", ""))[:500]
        if not title and not desc:
            return base
        # Clipboard helper params (user copies from app)
        return (
            f"{base}#resellpro="
            f"{quote(json.dumps({'title': title, 'description': desc, 'price': draft.get('price', 0)}, ensure_ascii=False))}"
        )
