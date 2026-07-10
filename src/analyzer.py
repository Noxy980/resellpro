"""Expert listing analysis — demand, aesthetics, sales potential, reseller gate."""

from __future__ import annotations

import logging
import re
import statistics
from dataclasses import dataclass
from typing import Any

from .aesthetic import AestheticAnalyzer
from .cache import TTLCache
from .config import AppConfig, BrandConfig
from .demand import DemandAnalyzer
from .image_analyzer import ImageAnalyzer
from .knowledge_base import KnowledgeBaseStore
from .sales_potential import SalesPotentialAnalyzer
from .scorer import ExpertScore, ExpertScorer
from .seasonal import get_current_season, season_match_score
from .search_optimizer import SearchOptimizer
from .vinted_client import VintedClient

logger = logging.getLogger(__name__)


@dataclass
class ListingAnalysis:
    listing_id: int
    title: str
    brand: str
    model: str
    category: str
    size: str
    condition: str
    price: float
    currency: str
    url: str
    image_url: str | None
    estimated_resale_value: float
    potential_profit: float
    profit_percent: float
    opportunity_score: int
    comparable_count: int
    comparable_median: float
    demand_level: str
    selling_speed: str
    quick_sale_probability: float
    estimated_days_to_sell: int
    ease_of_resale: float
    why_buy: str
    risk: str
    score_breakdown: dict[str, float]
    is_typo_listing: bool
    is_underpriced: bool
    expert_score: ExpertScore


def _parse_price(item: dict[str, Any]) -> tuple[float, str]:
    price = item.get("price") or {}
    return float(price.get("amount", 0)), price.get("currency_code", "EUR")


def _extract_image_url(item: dict[str, Any]) -> str | None:
    photo = item.get("photo") or {}
    if photo.get("url"):
        return photo["url"]
    photos = item.get("photos") or []
    return photos[0].get("url") if photos else None


def _extract_model(title: str, brand: str, detected: str | None = None) -> str:
    if detected:
        return detected
    model = re.sub(re.escape(brand), "", title, flags=re.IGNORECASE) if brand else title
    model = re.sub(r"[^\w\s\-/]", " ", model)
    return re.sub(r"\s+", " ", model).strip() or title


def _guess_category(title: str) -> str:
    mapping = {
        "veste": ["veste", "jacket", "blouson", "parka", "manteau", "coat", "shell"],
        "sweat": ["sweat", "hoodie", "pull", "crewneck", "zip"],
        "pantalon": ["pantalon", "jean", "trouser", "cargo", "jogger"],
        "sneaker": ["sneaker", "basket", "shoe", "chaussure", "trainer"],
        "polo": ["polo"],
        "chemise": ["chemise", "shirt", "tee", "t-shirt", "t shirt"],
    }
    text = title.lower()
    for cat, kws in mapping.items():
        if any(k in text for k in kws):
            return cat
    return "autre"


class ListingAnalyzer:
    def __init__(
        self,
        config: AppConfig,
        client: VintedClient,
        knowledge_store: KnowledgeBaseStore,
    ) -> None:
        self.config = config
        self.client = client
        self.knowledge_store = knowledge_store
        self.knowledge = knowledge_store.kb

        self.demand_analyzer = DemandAnalyzer(config, self.knowledge)
        self.aesthetic_analyzer = AestheticAnalyzer(config)
        self.image_analyzer = ImageAnalyzer(config.rare_models, config.title_red_flags)
        self.sales_analyzer = SalesPotentialAnalyzer(config, self.knowledge)
        self.scorer = ExpertScorer(config)
        self.search_optimizer = SearchOptimizer(config)
        self._season = get_current_season()

        self._brand_lookup = {b.name.lower(): b for b in config.target_brands}
        self._comparable_cache: TTLCache[list[dict[str, Any]]] = TTLCache(
            ttl_seconds=config.cache_ttl_seconds, max_size=300,
        )

    def _get_brand_config(self, brand: str) -> BrandConfig:
        return self._brand_lookup.get(brand.lower(), BrandConfig(name=brand, popularity=50, resale_ease=50))

    def _condition_multiplier(self, condition: str) -> float:
        key = condition.lower().strip()
        for pattern, value in self.config.condition_multipliers.items():
            if pattern != "default" and pattern in key:
                return value
        return self.config.condition_multipliers.get(key, self.config.condition_multipliers.get("default", 0.70))

    def _has_red_flags(self, title: str) -> bool:
        text = title.lower()
        return any(flag in text for flag in self.config.title_red_flags)

    def _fetch_comparables(self, brand: str, model: str, exclude_id: int) -> list[dict[str, Any]]:
        cache_key = f"{brand}|{model}"
        cached = self._comparable_cache.get(cache_key)
        if cached is not None:
            return [i for i in cached if i.get("id") != exclude_id]

        query = f"{brand} {model}".strip() or brand
        try:
            items = self.client.search_catalog(query, per_page=96, order="relevance")
            self._comparable_cache.set(cache_key, items)
            return [i for i in items if i.get("id") != exclude_id]
        except Exception as exc:
            logger.warning("Comparable search failed for '%s': %s", query, exc)
            return []

    def quick_screen(self, item: dict[str, Any]) -> bool:
        brand = item.get("brand_title") or ""
        model_hint = (item.get("title") or "")[:40]
        kb_price = self.knowledge.suggested_buy_price(brand, model_hint)
        result = self.search_optimizer.pre_screen(
            item, brand_lookup=self._brand_lookup, kb_suggested_price=kb_price,
        )
        return result.is_candidate

    def analyze(self, item: dict[str, Any], *, relaxed: bool = False) -> ListingAnalysis | None:
        listing_id = int(item["id"])
        price, currency = _parse_price(item)
        brand = item.get("brand_title") or ""
        title = self.search_optimizer.normalize_title(item.get("title") or "")
        brand_cfg = self._get_brand_config(brand)

        prescreen = self.search_optimizer.pre_screen(
            item,
            brand_lookup=self._brand_lookup,
            kb_suggested_price=self.knowledge.suggested_buy_price(brand, title),
        )
        if not prescreen.is_candidate:
            return None

        red_flags = self._has_red_flags(title)
        if red_flags:
            return None

        hot = self.demand_analyzer.match_hot_model(title, brand)
        model = _extract_model(title, brand, hot.canonical if hot else prescreen.matched_model)

        comparables = self._fetch_comparables(brand, model, listing_id)
        market = self.demand_analyzer.build_comparable_market(comparables, brand)

        if market.count < self.config.criteria.min_comparable_samples:
            if hot and hot.avg_resale_price > 0:
                market.median_price = hot.avg_resale_price
                market.count = self.config.criteria.min_comparable_samples
            else:
                kb_resale = self.knowledge.expected_resale(brand, model)
                if kb_resale:
                    market.median_price = kb_resale
                    market.count = self.config.criteria.min_comparable_samples
                else:
                    return None

        condition = item.get("status") or "Unknown"
        condition_mult = self._condition_multiplier(condition)
        estimated_resale = market.median_price * condition_mult
        estimated_resale *= (1 - self.config.resale.conservative_discount_percent / 100)

        if hot and hot.avg_resale_price > estimated_resale:
            estimated_resale = hot.avg_resale_price * condition_mult * 0.95

        selling_costs = estimated_resale * (self.config.resale.selling_cost_percent / 100)
        profit = estimated_resale - selling_costs - self.config.resale.fixed_cost_per_item - price
        profit_pct = (profit / price * 100) if price > 0 else 0

        if profit < self.config.criteria.min_expected_profit:
            return None
        if profit_pct < self.config.criteria.min_profit_percent:
            return None

        is_underpriced = price < market.median_price * 0.65 or prescreen.is_underpriced_hint

        photos = item.get("photos") or []
        photo_count = len(photos) or (1 if item.get("photo") else 0)
        dominant = None
        max_res = 0
        for p in photos:
            dominant = dominant or p.get("dominant_color")
            max_res = max(max_res, max(int(p.get("width") or 0), int(p.get("height") or 0)))

        category = _guess_category(title)
        season_score = season_match_score(title, category, self._season)
        if season_score < 25:
            logger.debug("Off-season item rejected: %s (season %s, score %d)", title, self._season.name, season_score)
            return None

        demand = self.demand_analyzer.assess(
            title=title, brand=brand, model=model,
            category=category,
            favourite_count=int(item.get("favourite_count") or 0),
            view_count=int(item.get("view_count") or 0),
            market=market, brand_popularity=brand_cfg.popularity,
        )

        aesthetic = self.aesthetic_analyzer.assess(
            title=title, category=category,
            photo_count=photo_count, dominant_color=dominant,
            photo_resolution=max_res,
        )

        if aesthetic.is_hard_to_sell and aesthetic.score < 40:
            return None
        if aesthetic.is_kids_item:
            return None

        image = self.image_analyzer.assess(
            item, title=title, brand=brand,
            hot_canonical=hot.canonical if hot else None,
            has_red_flags=red_flags,
        )

        if image.authenticity_risk == "high":
            return None

        sales = self.sales_analyzer.assess(
            brand_cfg=brand_cfg, brand=brand, model=model,
            profit=profit, profit_percent=profit_pct,
            demand=demand, aesthetic_score=aesthetic.score,
            listing_quality=image.score,
            purchase_price=price, estimated_resale=estimated_resale,
            is_underpriced=is_underpriced,
        )

        expert = self.scorer.score(
            brand_cfg=brand_cfg, brand=brand, model=model,
            profit=profit, profit_percent=profit_pct,
            purchase_price=price, estimated_resale=estimated_resale,
            demand=demand, sales=sales, aesthetic=aesthetic,
            image=image, comparable_count=market.count,
            has_red_flags=red_flags, is_underpriced=is_underpriced,
            is_typo=prescreen.is_typo_listing,
            season_score=season_score,
            season_name=self._season.name,
        )

        if not expert.reseller_approved:
            if not relaxed or expert.total < 65 or profit < 12:
                logger.debug(
                    "Rejected by reseller gate: %s (score %d, days %d, demand %s)",
                    title, expert.total, sales.estimated_days_to_sell, demand.level,
                )
                return None
            logger.info("Relaxed pass: %s (score %d)", title, expert.total)

        self.knowledge_store.kb.learn(
            brand, model, price, estimated_resale, profit, sales.estimated_days_to_sell,
        )

        return ListingAnalysis(
            listing_id=listing_id,
            title=title,
            brand=brand,
            model=model,
            category=_guess_category(title),
            size=item.get("size_title") or "N/A",
            condition=condition,
            price=price,
            currency=currency,
            url=item.get("url") or "",
            image_url=_extract_image_url(item),
            estimated_resale_value=round(estimated_resale, 2),
            potential_profit=round(profit, 2),
            profit_percent=round(profit_pct, 1),
            opportunity_score=expert.total,
            comparable_count=market.count,
            comparable_median=round(market.median_price, 2),
            demand_level=demand.level,
            selling_speed=sales.speed_label,
            quick_sale_probability=sales.quick_sale_probability,
            estimated_days_to_sell=sales.estimated_days_to_sell,
            ease_of_resale=sales.ease_of_resale,
            why_buy=expert.why_buy,
            risk=expert.risk,
            score_breakdown={
                "brand": expert.brand,
                "demand": expert.demand,
                "profit": expert.profit,
                "resale_speed": expert.resale_speed,
                "style": expert.style,
                "listing_quality": expert.listing_quality,
                "season": expert.season,
            },
            is_typo_listing=prescreen.is_typo_listing,
            is_underpriced=is_underpriced,
            expert_score=expert,
        )
