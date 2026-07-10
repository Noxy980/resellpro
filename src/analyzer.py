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
from .market_pricing import VintedMarketPricer
from .gem_hunter import is_pepite_listing, is_year_round_item, pepite_category, pepite_demand_boost
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
        "maillot": ["maillot", "jersey", "football shirt", "football", "nba"],
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
        self.market_pricer = VintedMarketPricer(client)
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

    def analyze(self, item: dict[str, Any], *, relaxed: bool = False, gem_hunt: bool = True) -> ListingAnalysis | None:
        listing_id = int(item["id"])
        price, currency = _parse_price(item)
        brand = item.get("brand_title") or ""
        title = self.search_optimizer.normalize_title(item.get("title") or "")
        brand_cfg = self._get_brand_config(brand)
        fav_count = int(item.get("favourite_count") or 0)
        is_pepite = is_pepite_listing(title, brand, fav_count)

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

        # ── Prix réels Vinted : combien vendent les autres ce produit ? ──
        mpa = self.market_pricer.analyze(
            purchase_price=price,
            brand=brand,
            model=model,
            title=title,
            exclude_id=listing_id,
            min_comparables=max(3, self.config.criteria.min_comparable_samples),
        )

        condition = item.get("status") or "Unknown"
        condition_mult = self._condition_multiplier(condition)

        ok, estimated_resale, profit, reject_reason = self.market_pricer.passes_margin_gate(
            mpa,
            price,
            min_discount_percent=8.0,
            min_profit_eur=self.config.criteria.min_expected_profit,
            min_profit_after_fees_percent=self.config.criteria.min_profit_percent,
            selling_cost_percent=self.config.resale.selling_cost_percent,
            fixed_cost=self.config.resale.fixed_cost_per_item,
            condition_mult=condition_mult,
            conservative_discount=self.config.resale.conservative_discount_percent,
        )

        if not ok:
            logger.debug("Rejected (marché Vinted): %s — %s", title[:50], reject_reason)
            return None

        profit_pct = (profit / price * 100) if price > 0 else 0
        is_underpriced = mpa.is_underpriced or prescreen.is_underpriced_hint

        # Demand analysis avec données marché réelles
        comparables = self._fetch_comparables(brand, model, listing_id)
        market = self.demand_analyzer.build_comparable_market(comparables, brand)
        if mpa.has_real_data:
            market.median_price = mpa.median_price
            market.count = max(market.count, mpa.count)

        photos = item.get("photos") or []
        photo_count = len(photos) or (1 if item.get("photo") else 0)
        dominant = None
        max_res = 0
        for p in photos:
            dominant = dominant or p.get("dominant_color")
            max_res = max(max_res, max(int(p.get("width") or 0), int(p.get("height") or 0)))

        category = _guess_category(title) or pepite_category(title) or "autre"
        season_score = season_match_score(title, category, self._season)
        if is_pepite:
            season_score = max(season_score, 65)
        if season_score < 25 and not is_year_round_item(title) and not is_pepite:
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
            is_pepite=is_pepite,
            pepite_boost=pepite_demand_boost(title, fav_count),
        )

        use_relaxed = relaxed or gem_hunt
        if not expert.reseller_approved:
            min_score = 52 if is_pepite else 58
            min_profit = 5 if is_pepite else 7
            if not use_relaxed or expert.total < min_score or profit < min_profit:
                logger.debug(
                    "Rejected by reseller gate: %s (score %d, days %d, demand %s, pepite=%s)",
                    title, expert.total, sales.estimated_days_to_sell, demand.level, is_pepite,
                )
                return None
            logger.info("Gem pass: %s (score %d, pepite=%s)", title, expert.total, is_pepite)

        market_context = (
            f"Marché Vinted: {mpa.count} similaires à €{mpa.median_price:.0f} médiane "
            f"(achat €{price:.0f}, -{mpa.discount_vs_market:.0f}% vs marché, profit net €{profit:.0f})"
        )
        why_buy = f"{market_context}; {expert.why_buy}"

        self.knowledge_store.kb.learn(
            brand, model, price, estimated_resale, profit, sales.estimated_days_to_sell,
        )

        return ListingAnalysis(
            listing_id=listing_id,
            title=title,
            brand=brand,
            model=model,
            category=category,
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
            comparable_count=mpa.count,
            comparable_median=mpa.median_price,
            demand_level=demand.level,
            selling_speed=sales.speed_label,
            quick_sale_probability=sales.quick_sale_probability,
            estimated_days_to_sell=sales.estimated_days_to_sell,
            ease_of_resale=sales.ease_of_resale,
            why_buy=why_buy,
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
