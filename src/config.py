"""Load and validate configuration from config.yaml."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class BrandConfig:
    name: str
    popularity: int = 70
    resale_ease: int = 70


@dataclass
class HotModelConfig:
    brand: str
    canonical: str
    aliases: list[str] = field(default_factory=list)
    demand_boost: int = 20
    avg_resale_price: float = 0.0
    resale_speed_days: int = 21


@dataclass
class CriteriaConfig:
    max_purchase_price: float = 80.0
    min_expected_profit: float = 15.0
    min_profit_percent: float = 25.0
    min_opportunity_score: int = 75
    min_comparable_samples: int = 5
    min_quick_sale_probability: float = 50.0
    max_days_to_sell: int = 45
    max_alerts_per_cycle: int = 3


@dataclass
class ResaleConfig:
    selling_cost_percent: float = 10.0
    fixed_cost_per_item: float = 2.0
    conservative_discount_percent: float = 5.0


@dataclass
class AppConfig:
    country: str = "fr"
    poll_interval_seconds: int = 90
    listings_per_search: int = 48
    request_delay_seconds: float = 1.5
    max_analyses_per_brand: int = 12
    min_prescreen_score: float = 25.0
    enable_typo_searches: bool = True
    discord_webhook_url: str = ""
    target_brands: list[BrandConfig] = field(default_factory=list)
    hot_models: list[HotModelConfig] = field(default_factory=list)
    criteria: CriteriaConfig = field(default_factory=CriteriaConfig)
    target_categories: list[str] = field(default_factory=list)
    title_red_flags: list[str] = field(default_factory=list)
    trending_styles: list[str] = field(default_factory=list)
    dated_styles: list[str] = field(default_factory=list)
    appealing_colors: list[str] = field(default_factory=list)
    hard_to_sell_signals: list[str] = field(default_factory=list)
    rare_models: list[str] = field(default_factory=list)
    category_demand: dict[str, float] = field(default_factory=dict)
    resale: ResaleConfig = field(default_factory=ResaleConfig)
    condition_multipliers: dict[str, float] = field(default_factory=dict)
    seen_listings_file: str = "data/seen_listings.json"
    knowledge_base_file: str = "data/knowledge_base.json"
    cache_ttl_seconds: int = 3600

    @property
    def base_url(self) -> str:
        return f"https://www.vinted.{self.country}"


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_config(config_path: str | Path | None = None) -> AppConfig:
    import os
    root = Path(os.environ.get("RESELLPRO_ROOT", _project_root()))
    path = Path(config_path) if config_path else root / "config.yaml"

    with open(path, encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f) or {}

    vinted = raw.get("vinted", {})
    discord = raw.get("discord", {})
    criteria = raw.get("criteria", {})
    resale = raw.get("resale", {})
    storage = raw.get("storage", {})
    demand_cfg = raw.get("demand", {})
    aesthetic_cfg = raw.get("aesthetic", {})

    webhook = os.environ.get("VINTED_DISCORD_WEBHOOK") or discord.get("webhook_url", "")

    brands = [
        BrandConfig(
            name=b["name"],
            popularity=int(b.get("popularity", 70)),
            resale_ease=int(b.get("resale_ease", 70)),
        )
        for b in raw.get("target_brands", [])
    ]

    hot_models = [
        HotModelConfig(
            brand=m["brand"],
            canonical=m["canonical"],
            aliases=m.get("aliases", []),
            demand_boost=int(m.get("demand_boost", 20)),
            avg_resale_price=float(m.get("avg_resale_price", 0)),
            resale_speed_days=int(m.get("resale_speed_days", 21)),
        )
        for m in raw.get("hot_models", [])
    ]

    condition_multipliers = raw.get("condition_multipliers", {})
    if not condition_multipliers:
        condition_multipliers = {"default": 0.70}

    return AppConfig(
        country=vinted.get("country", "fr"),
        poll_interval_seconds=int(vinted.get("poll_interval_seconds", 90)),
        listings_per_search=int(vinted.get("listings_per_search", 48)),
        request_delay_seconds=float(vinted.get("request_delay_seconds", 1.5)),
        max_analyses_per_brand=int(vinted.get("max_analyses_per_brand", 12)),
        min_prescreen_score=float(vinted.get("min_prescreen_score", 25)),
        enable_typo_searches=bool(vinted.get("enable_typo_searches", True)),
        discord_webhook_url=webhook,
        target_brands=brands,
        hot_models=hot_models,
        criteria=CriteriaConfig(
            max_purchase_price=float(criteria.get("max_purchase_price", 80)),
            min_expected_profit=float(criteria.get("min_expected_profit", 15)),
            min_profit_percent=float(criteria.get("min_profit_percent", 25)),
            min_opportunity_score=int(criteria.get("min_opportunity_score", 75)),
            min_comparable_samples=int(criteria.get("min_comparable_samples", 5)),
            min_quick_sale_probability=float(criteria.get("min_quick_sale_probability", 50)),
            max_days_to_sell=int(criteria.get("max_days_to_sell", 45)),
            max_alerts_per_cycle=int(criteria.get("max_alerts_per_cycle", 3)),
        ),
        target_categories=[c.lower() for c in raw.get("target_categories", [])],
        title_red_flags=[f.lower() for f in raw.get("title_red_flags", [])],
        trending_styles=aesthetic_cfg.get("trending_styles", raw.get("trending_styles", [])),
        dated_styles=aesthetic_cfg.get("dated_styles", raw.get("dated_styles", [])),
        appealing_colors=aesthetic_cfg.get("appealing_colors", []),
        hard_to_sell_signals=aesthetic_cfg.get("hard_to_sell_signals", []),
        rare_models=demand_cfg.get("rare_models", raw.get("rare_models", [])),
        category_demand={k: float(v) for k, v in demand_cfg.get("category_demand", {}).items()},
        resale=ResaleConfig(
            selling_cost_percent=float(resale.get("selling_cost_percent", 10)),
            fixed_cost_per_item=float(resale.get("fixed_cost_per_item", 2)),
            conservative_discount_percent=float(resale.get("conservative_discount_percent", 5)),
        ),
        condition_multipliers={k.lower(): float(v) for k, v in condition_multipliers.items()},
        seen_listings_file=storage.get("seen_listings_file", "data/seen_listings.json"),
        knowledge_base_file=storage.get("knowledge_base_file", "data/knowledge_base.json"),
        cache_ttl_seconds=int(storage.get("cache_ttl_seconds", 3600)),
    )


def resolve_path(relative: str) -> Path:
    import os
    root = Path(os.environ.get("RESELLPRO_ROOT", _project_root()))
    return root / relative
