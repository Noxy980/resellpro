"""Demand analysis — trending brands, models, styles, and market velocity."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .config import AppConfig, HotModelConfig
from .knowledge_base import KnowledgeBase


@dataclass
class ComparableMarket:
    prices: list[float]
    favourites: list[int]
    views: list[int]
    count: int
    median_price: float
    avg_favourites: float
    avg_views: float
    engagement_rate: float  # favourites per listing relative to views


@dataclass
class DemandAssessment:
    level: str  # low / medium / high
    score: float  # 0-100
    trending_model_match: str | None
    category_demand: float
    market_velocity: float
    brand_trend_score: float
    is_fast_moving_category: bool


class DemandAnalyzer:
    def __init__(self, config: AppConfig, knowledge: KnowledgeBase) -> None:
        self.config = config
        self.knowledge = knowledge
        self._hot_models = {m.canonical.lower(): m for m in config.hot_models}
        self._category_demand = {k.lower(): v for k, v in config.category_demand.items()}

    def match_hot_model(self, title: str, brand: str) -> HotModelConfig | None:
        text = f"{brand} {title}".lower()
        best: HotModelConfig | None = None
        best_score = 0

        for model in self.config.hot_models:
            score = 0
            if model.brand.lower() not in brand.lower() and brand.lower() not in model.brand.lower():
                continue
            if model.canonical.lower() in text:
                score = 100
            else:
                for alias in model.aliases:
                    if alias.lower() in text:
                        score = max(score, 80)
            if score > best_score:
                best_score = score
                best = model

        return best if best_score >= 80 else None

    def build_comparable_market(self, items: list[dict[str, Any]], brand: str) -> ComparableMarket:
        prices, favourites, views = [], [], []
        for item in items:
            item_brand = (item.get("brand_title") or "").lower()
            if brand.lower() not in item_brand and item_brand not in brand.lower():
                continue
            price_data = item.get("price") or {}
            price = float(price_data.get("amount", 0))
            if price > 0:
                prices.append(price)
                favourites.append(int(item.get("favourite_count") or 0))
                views.append(int(item.get("view_count") or 0))

        if not prices:
            return ComparableMarket([], [], [], 0, 0, 0, 0, 0)

        import statistics

        median = statistics.median(prices)
        avg_fav = sum(favourites) / len(favourites)
        avg_views = sum(views) / len(views)
        engagement = (avg_fav / max(avg_views, 1)) * 100

        return ComparableMarket(
            prices=prices,
            favourites=favourites,
            views=views,
            count=len(prices),
            median_price=median,
            avg_favourites=avg_fav,
            avg_views=avg_views,
            engagement_rate=engagement,
        )

    def assess(
        self,
        *,
        title: str,
        brand: str,
        model: str,
        category: str,
        favourite_count: int,
        view_count: int,
        market: ComparableMarket,
        brand_popularity: int,
    ) -> DemandAssessment:
        hot = self.match_hot_model(title, brand)
        kb = self.knowledge.get(brand, model)

        category_demand = self._category_demand.get(category.lower(), 50.0)
        for kw, score in self._category_demand.items():
            if kw in title.lower():
                category_demand = max(category_demand, score)

        market_velocity = 0.0
        if market.count > 0:
            market_velocity = min(100, market.engagement_rate * 15 + market.avg_favourites * 3)

        listing_velocity = min(100, favourite_count * 8 + view_count * 0.5)
        velocity = market_velocity * 0.6 + listing_velocity * 0.4

        brand_trend = float(brand_popularity)
        if hot:
            brand_trend = min(100, brand_trend + hot.demand_boost)

        kb_boost = 0.0
        if kb and kb.samples >= 2:
            kb_boost = min(30, kb.success_rate * 30)
            if kb.avg_days_to_sell <= 14:
                kb_boost += 15
            elif kb.avg_days_to_sell <= 30:
                kb_boost += 8

        score = (
            brand_trend * 0.25
            + velocity * 0.30
            + category_demand * 0.20
            + (hot.demand_boost if hot else 30) * 0.15
            + kb_boost * 0.10
        )
        score = min(100, score)

        if score >= 70:
            level = "high"
        elif score >= 45:
            level = "medium"
        else:
            level = "low"

        fast_categories = {"sneaker", "hoodie", "veste", "sweat"}
        is_fast = category.lower() in fast_categories or (hot is not None and hot.resale_speed_days <= 21)

        return DemandAssessment(
            level=level,
            score=round(score, 1),
            trending_model_match=hot.canonical if hot else None,
            category_demand=category_demand,
            market_velocity=round(velocity, 1),
            brand_trend_score=round(brand_trend, 1),
            is_fast_moving_category=is_fast,
        )
