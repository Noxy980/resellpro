"""Search optimization — typo detection, pre-screening, prioritization, seasonal."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .config import AppConfig, HotModelConfig
from .seasonal import get_current_season, season_match_score


@dataclass
class PreScreenResult:
    score: float
    is_candidate: bool
    is_typo_listing: bool
    matched_model: str | None
    is_underpriced_hint: bool
    skip_reason: str | None
    season_score: float = 50.0


class SearchOptimizer:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._brand_names = {b.name.lower() for b in config.target_brands}
        self._season = get_current_season()

    def seasonal_search_queries(self) -> list[str]:
        """Build season-aware searches combining brands + trending keywords."""
        queries: list[str] = []
        brands = [b.name for b in self.config.target_brands[:6]]
        for brand in brands:
            for kw in self._season.keywords[:5]:
                queries.append(f"{brand} {kw}")
        for kw in self._season.keywords[:8]:
            queries.append(kw)
        return list(dict.fromkeys(queries))

    def typo_search_queries(self) -> list[str]:
        """Extra searches targeting common seller typos on hot models."""
        queries: list[str] = []
        for model in self.config.hot_models:
            for alias in model.aliases:
                if alias != model.canonical:
                    queries.append(f"{model.brand} {alias}")
        return queries

    def detect_typo_match(self, title: str, brand: str) -> HotModelConfig | None:
        text = f"{brand} {title}".lower()
        for model in self.config.hot_models:
            if model.brand.lower() not in brand.lower():
                continue
            for alias in model.aliases:
                if alias.lower() in text and alias.lower() != model.canonical.lower():
                    return model
        return None

    def normalize_title(self, title: str) -> str:
        result = title
        for model in self.config.hot_models:
            for alias in model.aliases:
                if alias.lower() in result.lower():
                    result = re.sub(re.escape(alias), model.canonical, result, flags=re.IGNORECASE)
        return result

    def pre_screen(
        self,
        item: dict[str, Any],
        *,
        brand_lookup: dict[str, Any],
        kb_suggested_price: float | None = None,
    ) -> PreScreenResult:
        price_data = item.get("price") or {}
        price = float(price_data.get("amount", 0))
        title = item.get("title") or ""
        brand = item.get("brand_title") or ""
        criteria = self.config.criteria

        if price <= 0 or price > criteria.max_purchase_price:
            return PreScreenResult(0, False, False, None, False, "price out of range")

        if self.config.target_categories:
            title_lower = title.lower()
            season_ok = any(kw in title_lower for kw in self._season.keywords)
            cat_ok = any(cat in title_lower for cat in self.config.target_categories)
            if not cat_ok and not season_ok:
                return PreScreenResult(0, False, False, None, False, "category mismatch")

        if brand.lower() not in brand_lookup and self.config.target_brands:
            title_lower = title.lower()
            brand_in_title = any(b.name.lower() in title_lower for b in self.config.target_brands)
            if not brand_in_title:
                return PreScreenResult(0, False, False, None, False, "brand not targeted")

        text = title.lower()
        if any(flag in text for flag in self.config.title_red_flags):
            return PreScreenResult(0, False, False, None, False, "red flag in title")

        category = title.lower()
        season_score = season_match_score(title, category, self._season)
        if season_score < 20:
            return PreScreenResult(0, False, False, None, False, "off-season item")

        score = 30.0 + (season_score - 50) * 0.4
        for boost_brand in self._season.brands_boost:
            if boost_brand.lower() in brand.lower():
                score += 12
                break

        typo_model = self.detect_typo_match(title, brand)
        is_typo = typo_model is not None
        matched = typo_model.canonical if typo_model else None

        if is_typo:
            score += 25

        for model in self.config.hot_models:
            if model.brand.lower() in brand.lower():
                if model.canonical.lower() in text:
                    score += 20
                    matched = model.canonical

        fav = int(item.get("favourite_count") or 0)
        score += min(15, fav * 3)

        is_underpriced = False
        if kb_suggested_price and price < kb_suggested_price * 0.7:
            score += 20
            is_underpriced = True

        is_candidate = score >= self.config.min_prescreen_score

        return PreScreenResult(
            score=score,
            is_candidate=is_candidate,
            is_typo_listing=is_typo,
            matched_model=matched,
            is_underpriced_hint=is_underpriced,
            skip_reason=None if is_candidate else "low prescreen score",
            season_score=season_score,
        )

    def prioritize(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Sort listings: newest with highest early interest first."""

        def sort_key(item: dict[str, Any]) -> tuple:
            fav = int(item.get("favourite_count") or 0)
            price_data = item.get("price") or {}
            price = float(price_data.get("amount", 999))
            item_id = int(item.get("id") or 0)
            return (-fav, price, -item_id)

        return sorted(items, key=sort_key)
