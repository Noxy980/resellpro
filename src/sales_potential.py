"""Sales potential — quick sale probability, resale speed, buyer demand."""

from __future__ import annotations

from dataclasses import dataclass

from .config import AppConfig, BrandConfig
from .demand import DemandAssessment
from .knowledge_base import KnowledgeBase


@dataclass
class SalesPotential:
    quick_sale_probability: float  # 0-100 %
    estimated_days_to_sell: int
    demand_level: str
    ease_of_resale: float  # 0-100
    would_buyers_want_this: bool
    speed_label: str  # e.g. "3-7 days", "2-4 weeks"


class SalesPotentialAnalyzer:
    def __init__(self, config: AppConfig, knowledge: KnowledgeBase) -> None:
        self.config = config
        self.knowledge = knowledge

    def _days_to_label(self, days: int) -> str:
        if days <= 7:
            return "3-7 days"
        if days <= 14:
            return "1-2 weeks"
        if days <= 30:
            return "2-4 weeks"
        if days <= 60:
            return "1-2 months"
        return "3+ months"

    def assess(
        self,
        *,
        brand_cfg: BrandConfig,
        brand: str,
        model: str,
        profit: float,
        profit_percent: float,
        demand: DemandAssessment,
        aesthetic_score: float,
        listing_quality: float,
        purchase_price: float,
        estimated_resale: float,
        is_underpriced: bool,
    ) -> SalesPotential:
        kb = self.knowledge.get(brand, model)

        base_days = 45.0
        if kb and kb.samples >= 2:
            base_days = kb.avg_days_to_sell
        elif demand.trending_model_match:
            base_days = 18.0
        elif demand.is_fast_moving_category:
            base_days = 25.0
        else:
            base_days = 40.0

        base_days *= (100 - brand_cfg.resale_ease) / 30 + 0.5

        if demand.level == "high":
            base_days *= 0.55
        elif demand.level == "medium":
            base_days *= 0.80

        if aesthetic_score < 40:
            base_days *= 1.5
        elif aesthetic_score >= 70:
            base_days *= 0.75

        if listing_quality < 50:
            base_days *= 1.3

        if is_underpriced:
            base_days *= 0.7

        if profit_percent > 80:
            base_days *= 0.85

        days = max(3, int(round(base_days)))

        if days <= 10:
            prob = 85.0
        elif days <= 21:
            prob = 70.0
        elif days <= 35:
            prob = 55.0
        elif days <= 60:
            prob = 35.0
        else:
            prob = 15.0

        prob += (demand.score - 50) * 0.2
        prob += (aesthetic_score - 50) * 0.15
        prob += (listing_quality - 50) * 0.1
        if is_underpriced:
            prob += 10
        prob = min(95, max(5, prob))

        ease = (
            brand_cfg.resale_ease * 0.30
            + demand.score * 0.30
            + prob * 0.20
            + aesthetic_score * 0.20
        )

        would_buy = (
            demand.level != "low"
            and aesthetic_score >= 35
            and prob >= 45
            and profit > 0
            and days <= self.config.criteria.max_days_to_sell
        )

        return SalesPotential(
            quick_sale_probability=round(prob, 1),
            estimated_days_to_sell=days,
            demand_level=demand.level,
            ease_of_resale=round(ease, 1),
            would_buyers_want_this=would_buy,
            speed_label=self._days_to_label(days),
        )
