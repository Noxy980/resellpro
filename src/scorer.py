"""Expert opportunity scoring — 100-point reseller-grade evaluation."""

from __future__ import annotations

from dataclasses import dataclass

from .aesthetic import AestheticAssessment
from .config import AppConfig, BrandConfig
from .demand import DemandAssessment
from .image_analyzer import ImageAssessment
from .sales_potential import SalesPotential


@dataclass
class ExpertScore:
    total: int
    brand: float
    demand: float
    profit: float
    resale_speed: float
    style: float
    listing_quality: float
    why_buy: str
    risk: str
    reseller_approved: bool


class ExpertScorer:
    """Brand 15 | Demand 25 | Profit 20 | Speed 15 | Style 15 | Listing 10"""

    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def _clamp(self, v: float, lo: float = 0.0, hi: float = 100.0) -> float:
        return max(lo, min(hi, v))

    def _brand_points(self, brand_cfg: BrandConfig) -> float:
        return self._clamp(brand_cfg.popularity) * 0.15

    def _demand_points(self, demand: DemandAssessment) -> float:
        return self._clamp(demand.score) * 0.25

    def _profit_points(self, profit: float, profit_percent: float, purchase: float, resale: float) -> float:
        if profit <= 0:
            return 0.0
        margin_score = 0.0
        if profit_percent >= 100:
            margin_score = 100
        elif profit_percent >= 60:
            margin_score = 75 + (profit_percent - 60) * 0.6
        elif profit_percent >= 30:
            margin_score = 45 + (profit_percent - 30) * 1.0
        else:
            margin_score = profit_percent * 1.5

        absolute_bonus = min(20, profit / 2)
        raw = margin_score * 0.7 + absolute_bonus * 0.3
        return self._clamp(raw) * 0.20

    def _speed_points(self, sales: SalesPotential) -> float:
        days = sales.estimated_days_to_sell
        if days <= 7:
            raw = 100
        elif days <= 14:
            raw = 85
        elif days <= 21:
            raw = 70
        elif days <= 35:
            raw = 55
        elif days <= 60:
            raw = 30
        else:
            raw = 10
        raw = raw * 0.6 + sales.quick_sale_probability * 0.4
        return self._clamp(raw) * 0.15

    def _style_points(self, aesthetic: AestheticAssessment) -> float:
        score = aesthetic.score
        if aesthetic.is_dated:
            score *= 0.5
        if aesthetic.is_hard_to_sell:
            score *= 0.4
        if aesthetic.is_kids_item:
            score *= 0.5
        return self._clamp(score) * 0.15

    def _listing_points(self, image: ImageAssessment) -> float:
        score = image.score
        if image.authenticity_risk == "high":
            score *= 0.2
        elif image.authenticity_risk == "medium":
            score *= 0.6
        if image.has_defect_signals:
            score *= 0.5
        return self._clamp(score) * 0.10

    def _build_why_buy(
        self,
        *,
        brand: str,
        model: str,
        profit: float,
        profit_percent: float,
        demand: DemandAssessment,
        sales: SalesPotential,
        is_underpriced: bool,
        is_typo: bool,
        aesthetic: AestheticAssessment,
    ) -> str:
        reasons: list[str] = []
        if is_underpriced:
            reasons.append("Priced well below market median")
        if is_typo:
            reasons.append("Seller typo may hide this from other buyers")
        if demand.trending_model_match:
            reasons.append(f"Trending model: {demand.trending_model_match}")
        if sales.quick_sale_probability >= 65:
            reasons.append(f"High quick-sale probability ({sales.quick_sale_probability:.0f}%)")
        if profit_percent >= 50:
            reasons.append(f"Strong margin ({profit_percent:.0f}%)")
        if aesthetic.trend_match:
            reasons.append(f"On-trend style: {aesthetic.trend_match}")
        if demand.level == "high":
            reasons.append("High current demand")

        if not reasons:
            reasons.append(f"Solid {brand} flip with €{profit:.0f} estimated profit")

        return "; ".join(reasons[:3])

    def _build_risk(
        self,
        *,
        image: ImageAssessment,
        aesthetic: AestheticAssessment,
        sales: SalesPotential,
        comparable_count: int,
        has_red_flags: bool,
    ) -> str:
        risks: list[str] = []
        if image.authenticity_risk != "low":
            risks.append(f"Authenticity risk: {image.authenticity_risk}")
        if image.has_defect_signals:
            risks.append("Possible defects mentioned")
        if aesthetic.is_hard_to_sell:
            risks.append("Style may be hard to move")
        if aesthetic.is_kids_item:
            risks.append("Kids item — smaller buyer pool")
        if sales.estimated_days_to_sell > 45:
            risks.append(f"Slow resale (~{sales.speed_label})")
        if comparable_count < 8:
            risks.append("Limited comparable data")
        if has_red_flags:
            risks.append("Title contains warning signals")

        if not risks:
            return "Low risk — standard resale play"
        return "; ".join(risks[:3])

    def _reseller_gate(
        self,
        *,
        total: int,
        profit: float,
        sales: SalesPotential,
        aesthetic: AestheticAssessment,
        image: ImageAssessment,
        demand: DemandAssessment,
        has_red_flags: bool,
    ) -> bool:
        c = self.config.criteria
        if total < c.min_opportunity_score:
            return False
        if profit < c.min_expected_profit:
            return False
        if sales.quick_sale_probability < c.min_quick_sale_probability:
            return False
        if sales.estimated_days_to_sell > c.max_days_to_sell:
            return False
        if demand.level == "low":
            return False
        if aesthetic.is_hard_to_sell and aesthetic.score < 50:
            return False
        if aesthetic.is_kids_item:
            return False
        if image.authenticity_risk == "high":
            return False
        if has_red_flags:
            return False
        if not sales.would_buyers_want_this:
            return False
        return True

    def score(
        self,
        *,
        brand_cfg: BrandConfig,
        brand: str,
        model: str,
        profit: float,
        profit_percent: float,
        purchase_price: float,
        estimated_resale: float,
        demand: DemandAssessment,
        sales: SalesPotential,
        aesthetic: AestheticAssessment,
        image: ImageAssessment,
        comparable_count: int,
        has_red_flags: bool,
        is_underpriced: bool,
        is_typo: bool,
    ) -> ExpertScore:
        brand_pts = self._brand_points(brand_cfg)
        demand_pts = self._demand_points(demand)
        profit_pts = self._profit_points(profit, profit_percent, purchase_price, estimated_resale)
        speed_pts = self._speed_points(sales)
        style_pts = self._style_points(aesthetic)
        listing_pts = self._listing_points(image)

        total = int(round(brand_pts + demand_pts + profit_pts + speed_pts + style_pts + listing_pts))

        why = self._build_why_buy(
            brand=brand, model=model, profit=profit, profit_percent=profit_percent,
            demand=demand, sales=sales, is_underpriced=is_underpriced,
            is_typo=is_typo, aesthetic=aesthetic,
        )
        risk = self._build_risk(
            image=image, aesthetic=aesthetic, sales=sales,
            comparable_count=comparable_count, has_red_flags=has_red_flags,
        )

        approved = self._reseller_gate(
            total=total, profit=profit, sales=sales, aesthetic=aesthetic,
            image=image, demand=demand, has_red_flags=has_red_flags,
        )

        return ExpertScore(
            total=total,
            brand=round(brand_pts / 0.15, 1),
            demand=round(demand_pts / 0.25, 1),
            profit=round(profit_pts / 0.20, 1),
            resale_speed=round(speed_pts / 0.15, 1),
            style=round(style_pts / 0.15, 1),
            listing_quality=round(listing_pts / 0.10, 1),
            why_buy=why,
            risk=risk,
            reseller_approved=approved,
        )
