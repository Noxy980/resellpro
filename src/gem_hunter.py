"""Gem Hunter — recherches et détection des pépites Vinted (maillots, hype, vintage)."""

from __future__ import annotations

import re

from .seasonal import SeasonProfile, get_current_season

# Mots-clés qui signalent une pépite — bypass filtres catégorie/marque
PEPITE_SIGNALS: tuple[str, ...] = (
    "maillot", "jersey", "football shirt", "football", "soccer",
    "psg", "paris saint", "paris sg", "om ", " olympique", "marseille",
    "ol ", "lyon", "real madrid", "barcelona", "barça", "barca",
    "arsenal", "liverpool", "manchester", "chelsea", "juventus",
    "milan", "inter ", "bayern", "dortmund", "france 9", "équipe de france",
    "coupe du monde", "world cup", "euro 20", "nba", "nfl",
    "vintage", "retro", "90s", "90's", "2000s", "y2k", "archive",
    "deadstock", "rare", "limited edition", "édition limitée",
    "collab", "collaboration", "travis scott", "off-white", "off white",
    "jordan", "dunk low", "dunk high", "air max", "air force",
    "samba", "gazelle", "campus", "spezial", "handball",
    "nuptse", "tech fleece", "stone island", "cp company",
    "box logo", "supreme", "stüssy", "stussy", "carhartt",
    "arc'teryx", "arcteryx", "salomon", "xt-6", "xt-4",
    "new balance", "550", "574", "2002r", "9060",
    "ralph lauren", "polo bear", "lacoste", "crocodile",
    "gorpcore", "streetwear", "hype", "collector",
)

# Clubs / sélections — recherches directes Vinted FR
_FOOTBALL_CLUBS: tuple[str, ...] = (
    "psg", "paris", "om", "marseille", "ol", "lyon", "losc", "lille",
    "rennes", "nice", "monaco", "bordeaux", "saint-etienne",
    "real madrid", "barcelona", "barça", "arsenal", "liverpool",
    "manchester united", "manchester city", "chelsea", "tottenham",
    "juventus", "milan", "inter", "napoli", "roma", "bayern",
    "dortmund", "ajax", "benfica", "porto",
    "france", "allemagne", "espagne", "italie", "bresil", "argentine",
    "portugal", "belgique", "angleterre", "pays-bas",
)

_HYPE_SEARCHES: tuple[str, ...] = (
    "nike tech fleece", "nike dunk", "nike air max 90", "nike jordan",
    "adidas samba", "adidas gazelle", "adidas campus", "adidas spezial",
    "stone island", "cp company", "supreme box logo", "carhartt detroit",
    "the north face nuptse", "arc'teryx beta", "patagonia fleece",
    "new balance 550", "new balance 2002r", "salomon xt-6",
    "ralph lauren polo", "lacoste polo", "stussy tee",
    "vintage nike", "vintage adidas", "vintage carhartt",
    "y2k", "archive fashion", "streetwear", "gorpcore",
    "travis scott", "off white nike", "fear of god essentials",
)

_MAILLOT_SEARCHES: tuple[str, ...] = (
    "maillot vintage", "maillot retro", "maillot 90s", "maillot football",
    "maillot nike", "maillot adidas", "maillot puma", "maillot umbro",
    "maillot coupe du monde", "maillot world cup", "maillot france",
    "maillot psg", "maillot om", "maillot marseille", "maillot real madrid",
    "maillot barcelona", "maillot arsenal", "maillot liverpool",
    "maillot juventus", "maillot milan", "maillot collector",
    "football shirt vintage", "jersey nba", "maillot NBA",
    "maillot flocage", "maillot match worn", "maillot authentique",
)


def is_pepite_listing(title: str, brand: str = "", favourite_count: int = 0) -> bool:
    """True si l'annonce ressemble à une pépite recherchée."""
    text = f"{brand} {title}".lower()
    if any(sig in text for sig in PEPITE_SIGNALS):
        return True
    if favourite_count >= 8:
        return True
    if favourite_count >= 4 and any(k in text for k in ("maillot", "nike", "adidas", "vintage", "jordan", "dunk")):
        return True
    return False


def pepite_category(title: str) -> str | None:
    t = title.lower()
    if any(k in t for k in ("maillot", "jersey", "football", "nba", "nfl")):
        return "maillot"
    if any(k in t for k in ("dunk", "jordan", "air max", "samba", "gazelle", "sneaker", "basket")):
        return "sneaker"
    if any(k in t for k in ("nuptse", "veste", "jacket", "parka", "manteau")):
        return "veste"
    return None


def pepite_demand_boost(title: str, favourite_count: int) -> float:
    """Bonus 0-35 points pour scoring."""
    boost = 0.0
    text = title.lower()
    if "maillot" in text or "jersey" in text:
        boost += 18
    for club in _FOOTBALL_CLUBS:
        if club in text:
            boost += 12
            break
    if any(k in text for k in ("vintage", "retro", "90s", "coupe du monde", "world cup")):
        boost += 10
    if any(k in text for k in ("dunk", "samba", "nuptse", "tech fleece", "box logo")):
        boost += 8
    boost += min(15, favourite_count * 2.5)
    return min(35, boost)


def build_gem_queries(season: SeasonProfile | None = None) -> list[str]:
    """50+ requêtes orientées pépites pour Vinted FR."""
    season = season or get_current_season()
    queries: list[str] = []

    queries.extend(_MAILLOT_SEARCHES)
    for club in _FOOTBALL_CLUBS:
        queries.append(f"maillot {club}")
    queries.extend(_HYPE_SEARCHES)

    for brand in season.brands_boost[:8]:
        for kw in season.keywords[:4]:
            queries.append(f"{brand} {kw}")

    for kw in ("maillot", "vintage", "retro", "streetwear", "sneaker", "dunk", "samba"):
        queries.append(kw)

    return list(dict.fromkeys(queries))


def is_year_round_item(title: str) -> bool:
    """Maillots / sneakers hype — pas de rejet hors-saison."""
    t = title.lower()
    year_round = (
        "maillot", "jersey", "football", "nba", "dunk", "jordan", "samba",
        "gazelle", "air max", "air force", "supreme", "stone island",
        "vintage", "retro", "collector",
    )
    return any(k in t for k in year_round)
