"""Dynamic brand intelligence — resale speed, demand, margin, seasonal boosts."""

from __future__ import annotations

from dataclasses import dataclass

from .seasonal import SeasonProfile, get_current_season


@dataclass
class BrandIntel:
    name: str
    popularity: float
    resale_ease: float
    demand_tier: str  # hot | strong | moderate | slow | avoid
    margin_potential: str  # high | medium | low
    notes: str


# Curated reseller knowledge — not only luxury; fast mid-market brands included
_BRAND_DB: dict[str, BrandIntel] = {
    "Nike": BrandIntel("Nike", 92, 88, "hot", "high", "Sneakers & Tech Fleece = volume rapide"),
    "Adidas": BrandIntel("Adidas", 88, 85, "hot", "high", "Samba, Gazelle, tracksuits très demandés"),
    "Carhartt": BrandIntel("Carhartt", 84, 82, "strong", "medium", "Workwear tendance, bon volume"),
    "The North Face": BrandIntel("The North Face", 86, 80, "strong", "high", "Nuptse hiver, fleece mi-saison"),
    "Ralph Lauren": BrandIntel("Ralph Lauren", 80, 76, "strong", "medium", "Polo & pull = stable"),
    "Lacoste": BrandIntel("Lacoste", 78, 74, "moderate", "medium", "Polos été, classique"),
    "Stone Island": BrandIntel("Stone Island", 90, 85, "hot", "high", "Marge élevée, acheteurs exigeants"),
    "Patagonia": BrandIntel("Patagonia", 83, 79, "strong", "medium", "Outdoor durable, niche fidèle"),
    "Arc'teryx": BrandIntel("Arc'teryx", 88, 82, "hot", "high", "Technique premium, revente rapide"),
    "Supreme": BrandIntel("Supreme", 94, 88, "hot", "high", "Hype — attention aux contrefaçons"),
    "Stüssy": BrandIntel("Stüssy", 82, 78, "strong", "medium", "Streetwear stable"),
    "New Balance": BrandIntel("New Balance", 85, 83, "hot", "high", "550/574/2002R très recherchés"),
    "Puma": BrandIntel("Puma", 72, 70, "moderate", "low", "Volume ok, marges serrées"),
    "Zara": BrandIntel("Zara", 55, 45, "slow", "low", "Faible marge, lent à revendre"),
    "H&M": BrandIntel("H&M", 48, 40, "avoid", "low", "Éviter sauf pièce rare"),
    "Shein": BrandIntel("Shein", 35, 25, "avoid", "low", "Quasi impossible à revendre"),
    "Primark": BrandIntel("Primark", 40, 30, "avoid", "low", "Pas de marge"),
    "Uniqlo": BrandIntel("Uniqlo", 68, 62, "moderate", "low", "Bas prix, volume limité"),
    "Levi's": BrandIntel("Levi's", 76, 74, "strong", "medium", "501 & trucker = classiques"),
    "Dickies": BrandIntel("Dickies", 74, 72, "moderate", "medium", "Workwear accessible"),
    "Columbia": BrandIntel("Columbia", 70, 68, "moderate", "medium", "Outdoor entrée de gamme"),
    "Champion": BrandIntel("Champion", 72, 70, "moderate", "low", "Reverse weave ok, reste lent"),
    "Tommy Hilfiger": BrandIntel("Tommy Hilfiger", 74, 70, "moderate", "medium", "Logo pieces été"),
    "Hugo Boss": BrandIntel("Hugo Boss", 65, 58, "slow", "medium", "Lent hors classiques"),
    "Moncler": BrandIntel("Moncler", 88, 75, "strong", "high", "Hiver seulement, vérif auth"),
    "Canada Goose": BrandIntel("Canada Goose", 85, 72, "moderate", "high", "Saisonnier, risque contrefaçon"),
    "CP Company": BrandIntel("CP Company", 82, 78, "strong", "high", "Goggle jacket niche"),
    "Barbour": BrandIntel("Barbour", 72, 68, "moderate", "medium", "Automne/hiver UK"),
    "Salomon": BrandIntel("Salomon", 86, 84, "hot", "high", "XT-6 & sneakers trail hype"),
    "Asics": BrandIntel("Asics", 80, 78, "strong", "medium", "Gel-Kayano, 2000s running"),
}


def lookup_brand(name: str) -> BrandIntel | None:
    if not name:
        return None
    key = name.strip()
    if key in _BRAND_DB:
        return _BRAND_DB[key]
    for k, v in _BRAND_DB.items():
        if k.lower() == key.lower():
            return v
    return None


def effective_brand_scores(
    name: str,
    *,
    config_popularity: float,
    config_resale_ease: float,
    season: SeasonProfile | None = None,
    kb_boost: float = 0.0,
) -> tuple[float, float]:
    """Merge config, curated DB, season and learned data."""
    season = season or get_current_season()
    intel = lookup_brand(name)

    pop = config_popularity
    ease = config_resale_ease

    if intel:
        pop = pop * 0.4 + intel.popularity * 0.6
        ease = ease * 0.4 + intel.resale_ease * 0.6
        if intel.demand_tier == "hot":
            pop += 5
        elif intel.demand_tier == "avoid":
            pop -= 20
            ease -= 25

    if name in season.brands_boost or any(b.lower() in name.lower() for b in season.brands_boost):
        pop += 8
        ease += 5

    pop = min(100, max(0, pop + kb_boost))
    ease = min(100, max(0, ease + kb_boost * 0.5))
    return pop, ease


def get_fast_mover_brands(season: SeasonProfile | None = None) -> list[str]:
    season = season or get_current_season()
    hot = [b.name for b in _BRAND_DB.values() if b.demand_tier in ("hot", "strong")]
    boosted = [b for b in season.brands_boost if b not in hot]
    return list(dict.fromkeys(boosted + hot))[:20]


def get_seasonal_search_terms(season: SeasonProfile | None = None) -> list[str]:
    season = season or get_current_season()
    terms: list[str] = []
    for brand in season.brands_boost[:5]:
        for kw in season.keywords[:4]:
            terms.append(f"{brand} {kw}")
    for kw in season.keywords[:12]:
        terms.append(kw)
    return list(dict.fromkeys(terms))


def brand_rejection_penalty(name: str) -> float:
    """0-1 multiplier — low = reject."""
    intel = lookup_brand(name)
    if not intel:
        return 1.0
    if intel.demand_tier == "avoid":
        return 0.3
    if intel.demand_tier == "slow":
        return 0.65
    return 1.0
