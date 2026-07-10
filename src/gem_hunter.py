"""Gem Hunter — pépites diversifiées (pas que maillots) + signaux de demande."""

from __future__ import annotations

from .seasonal import SeasonProfile, get_current_season

# Signaux larges — streetwear, outdoor, sneakers, vintage, sport
PEPITE_SIGNALS: tuple[str, ...] = (
    "vintage", "retro", "90s", "90's", "2000s", "y2k", "archive", "deadstock",
    "rare", "limited", "collab", "travis scott", "off-white", "off white",
    "jordan", "dunk", "air max", "air force", "samba", "gazelle", "campus",
    "spezial", "handball", "nuptse", "tech fleece", "stone island", "cp company",
    "box logo", "supreme", "stüssy", "stussy", "carhartt", "detroit",
    "arc'teryx", "arcteryx", "salomon", "xt-6", "new balance", "550", "574",
    "2002r", "ralph lauren", "polo bear", "lacoste", "gorpcore", "streetwear",
    "maillot", "jersey", "football", "nba",
)

_SNEAKER_SEARCHES: tuple[str, ...] = (
    "nike dunk", "nike air max 90", "nike jordan", "nike air force",
    "adidas samba", "adidas gazelle", "adidas campus", "adidas spezial",
    "new balance 550", "new balance 2002r", "salomon xt-6", "asics gel",
    "puma suede", "converse", "vans old skool",
)

_OUTERWEAR_SEARCHES: tuple[str, ...] = (
    "stone island", "cp company", "the north face nuptse", "carhartt detroit",
    "carhartt jacket", "arc'teryx beta", "patagonia fleece", "barbour",
    "moncler", "ralph lauren jacket", "lacoste veste", "nike tech fleece",
)

_STREETWEAR_SEARCHES: tuple[str, ...] = (
    "supreme", "stussy", "palace", "carhartt wip", "vintage nike",
    "vintage adidas", "y2k", "archive fashion", "streetwear", "gorpcore",
    "travis scott", "fear of god essentials", "essentials hoodie",
)

_PANTS_SEARCHES: tuple[str, ...] = (
    "carhartt pantalon", "nike tech pant", "cargo pant", "levi's 501",
    "jean vintage", "jogging nike", "adidas pantalon", "dockers",
)

_MAILLOT_SEARCHES: tuple[str, ...] = (
    "maillot vintage", "maillot retro", "maillot football", "maillot nike",
    "maillot france", "maillot psg", "maillot om", "football shirt vintage",
)

_FOOTBALL_CLUBS: tuple[str, ...] = (
    "psg", "om", "marseille", "france", "real madrid", "barcelona",
    "arsenal", "liverpool", "juventus", "milan",
)


def is_pepite_listing(title: str, brand: str = "", favourite_count: int = 0) -> bool:
    text = f"{brand} {title}".lower()
    if favourite_count >= 10:
        return True
    if favourite_count >= 5 and any(k in text for k in ("nike", "adidas", "vintage", "dunk", "samba", "nuptse")):
        return True
    return sum(1 for sig in PEPITE_SIGNALS if sig in text) >= 2


def pepite_category(title: str) -> str | None:
    t = title.lower()
    if any(k in t for k in ("dunk", "jordan", "air max", "samba", "gazelle", "sneaker", "basket")):
        return "sneaker"
    if any(k in t for k in ("nuptse", "veste", "jacket", "parka", "manteau", "doudoune")):
        return "veste"
    if any(k in t for k in ("maillot", "jersey", "football")):
        return "maillot"
    if any(k in t for k in ("pantalon", "jean", "cargo", "jogger")):
        return "pantalon"
    if any(k in t for k in ("sweat", "hoodie", "pull")):
        return "sweat"
    return None


def pepite_demand_boost(title: str, favourite_count: int) -> float:
    boost = 0.0
    text = title.lower()
    if any(k in text for k in ("dunk", "samba", "nuptse", "tech fleece", "box logo", "jordan")):
        boost += 10
    if any(k in text for k in ("vintage", "retro", "90s", "archive")):
        boost += 8
    if "maillot" in text or "jersey" in text:
        boost += 6
    boost += min(12, favourite_count * 2)
    return min(25, boost)


def build_gem_queries(season: SeasonProfile | None = None) -> list[str]:
    """Requêtes diversifiées — ~20% maillots, reste streetwear/sneakers/outdoor."""
    season = season or get_current_season()
    queries: list[str] = []

    queries.extend(_SNEAKER_SEARCHES)
    queries.extend(_OUTERWEAR_SEARCHES)
    queries.extend(_STREETWEAR_SEARCHES)
    queries.extend(_PANTS_SEARCHES)
    queries.extend(_MAILLOT_SEARCHES)
    for club in _FOOTBALL_CLUBS[:6]:
        queries.append(f"maillot {club}")

    for brand in season.brands_boost[:6]:
        for kw in season.keywords[:3]:
            queries.append(f"{brand} {kw}")

    for kw in ("vintage", "streetwear", "sneaker", "dunk", "samba", "veste", "hoodie", "cargo"):
        queries.append(kw)

    return list(dict.fromkeys(queries))


def is_year_round_item(title: str) -> bool:
    t = title.lower()
    year_round = (
        "dunk", "jordan", "samba", "gazelle", "air max", "supreme", "stone island",
        "vintage", "retro", "maillot", "jersey", "tech fleece", "nuptse",
    )
    return any(k in t for k in year_round)
