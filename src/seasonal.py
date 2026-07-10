"""Seasonal intelligence — adapts search and scoring to current period."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class SeasonProfile:
    name: str
    keywords: list[str]
    categories: list[str]
    brands_boost: list[str]
    avoid_keywords: list[str]
    demand_multiplier: float


def get_current_season(today: date | None = None) -> SeasonProfile:
    today = today or date.today()
    month = today.month

    if month in (6, 7, 8):
        return SeasonProfile(
            name="été",
            keywords=[
                "t-shirt", "tee", "tshirt", "short", "shorts", "polo", "chemise",
                "sandales", "lunettes", "soleil", "lin", "débardeur", "maillot",
                "basket", "sneaker", "bermuda", "casquette", "cap", "short sleeve",
                "cargo short", "tank top", "slides", "bucket hat", "sunglasses",
                "swim", "boardshort", "veste légère", "windbreaker",
            ],
            categories=["t-shirt", "short", "polo", "chemise", "sneaker", "accessoire", "maillot"],
            brands_boost=["Nike", "Adidas", "Carhartt", "Lacoste", "Ralph Lauren", "New Balance", "Salomon"],
            avoid_keywords=[
                "doudoune", "parka", "manteau laine", "pull laine", "boots hiver",
                "bonnet", "écharpe", "gants", "puffer", "down jacket", "nuptse",
                "fleece heavy", "winter", "hiver", "ski",
            ],
            demand_multiplier=1.20,
        )
    if month in (12, 1, 2):
        return SeasonProfile(
            name="hiver",
            keywords=[
                "doudoune", "parka", "manteau", "coat", "veste", "jacket",
                "pull", "sweat", "hoodie", "boot", "chelsea", "nuptse",
                "fleece", "softshell", "gore-tex", "technique", "puffer",
                "down", "wool", "laine", "bonnet", "beanie", "écharpe",
            ],
            categories=["veste", "manteau", "pull", "sweat", "boot", "doudoune"],
            brands_boost=["The North Face", "Stone Island", "Arc'teryx", "Patagonia", "Carhartt", "Moncler", "Canada Goose"],
            avoid_keywords=["short", "bermuda", "maillot de bain", "t-shirt", "polo", "sandales", "débardeur"],
            demand_multiplier=1.25,
        )
    if month in (3, 4, 5):
        return SeasonProfile(
            name="printemps",
            keywords=[
                "veste", "jacket", "blouson", "sweat", "hoodie", "polo",
                "pantalon", "jean", "sneaker", "basket", "chemise", "cargo",
                "windbreaker", "zip", "cardigan", "bomber",
            ],
            categories=["veste", "sweat", "pantalon", "sneaker", "polo", "jean"],
            brands_boost=["Nike", "Carhartt", "Ralph Lauren", "Lacoste", "Stone Island", "New Balance"],
            avoid_keywords=["doudoune", "nuptse", "puffer", "maillot"],
            demand_multiplier=1.08,
        )
    return SeasonProfile(
        name="automne",
        keywords=[
            "veste", "jacket", "manteau", "pull", "sweat", "hoodie",
            "pantalon", "cargo", "boot", "chelsea", "fleece", "parka",
            "gilet", "overshirt", "flannel", "trench",
        ],
        categories=["veste", "pull", "sweat", "pantalon", "boot", "manteau"],
        brands_boost=["Carhartt", "The North Face", "Stone Island", "Nike", "Patagonia", "Barbour"],
        avoid_keywords=["short", "maillot", "sandales", "débardeur"],
        demand_multiplier=1.12,
    )


def season_match_score(title: str, category: str, season: SeasonProfile) -> float:
    text = f"{title} {category}".lower()
    score = 45.0
    hits = 0
    for kw in season.keywords:
        if kw in text:
            score += 7
            hits += 1
    for avoid in season.avoid_keywords:
        if avoid in text:
            score -= 22
    if hits >= 2:
        score += 10
    return max(0, min(100, score))


def is_off_season(title: str, category: str, season: SeasonProfile) -> bool:
    return season_match_score(title, category, season) < 30
