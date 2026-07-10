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
                "t-shirt", "tee", "short", "shorts", "polo", "chemise légère",
                "sandales", "lunettes", "soleil", "lin", "débardeur", "maillot",
                "basket", "sneaker", "bermuda", "casquette", "cap",
            ],
            categories=["t-shirt", "short", "polo", "chemise", "sneaker", "accessoire"],
            brands_boost=["Nike", "Adidas", "Carhartt", "Patagonia", "The North Face"],
            avoid_keywords=["doudoune", "parka", "manteau", "pull laine", "boots hiver"],
            demand_multiplier=1.15,
        )
    if month in (12, 1, 2):
        return SeasonProfile(
            name="hiver",
            keywords=[
                "doudoune", "parka", "manteau", "coat", "veste", "jacket",
                "pull", "sweat", "hoodie", "boot", "chelsea", "nuptse",
                "fleece", "softshell", "gore-tex", "technique",
            ],
            categories=["veste", "manteau", "pull", "sweat", "boot"],
            brands_boost=["The North Face", "Stone Island", "Arc'teryx", "Patagonia", "Carhartt"],
            avoid_keywords=["short", "bermuda", "maillot de bain"],
            demand_multiplier=1.20,
        )
    if month in (3, 4, 5):
        return SeasonProfile(
            name="printemps",
            keywords=[
                "veste", "jacket", "blouson", "sweat", "hoodie", "polo",
                "pantalon", "jean", "sneaker", "basket", "chemise",
            ],
            categories=["veste", "sweat", "pantalon", "sneaker", "polo"],
            brands_boost=["Nike", "Carhartt", "Ralph Lauren", "Lacoste", "Stone Island"],
            avoid_keywords=["doudoune", "short"],
            demand_multiplier=1.05,
        )
    # autumn
    return SeasonProfile(
        name="automne",
        keywords=[
            "veste", "jacket", "manteau", "pull", "sweat", "hoodie",
            "pantalon", "cargo", "boot", "chelsea", "fleece", "parka",
        ],
        categories=["veste", "pull", "sweat", "pantalon", "boot"],
        brands_boost=["Carhartt", "The North Face", "Stone Island", "Nike", "Patagonia"],
        avoid_keywords=["short", "maillot"],
        demand_multiplier=1.10,
    )


def season_match_score(title: str, category: str, season: SeasonProfile) -> float:
    text = f"{title} {category}".lower()
    score = 50.0
    for kw in season.keywords:
        if kw in text:
            score += 8
    for avoid in season.avoid_keywords:
        if avoid in text:
            score -= 15
    return max(0, min(100, score))
