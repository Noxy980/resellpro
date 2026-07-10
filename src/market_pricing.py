"""Analyse des prix réels sur Vinted — comparables vivants, pas d'estimation au pif."""

from __future__ import annotations

import logging
import re
import statistics
from dataclasses import dataclass
from typing import Any

from .vinted_client import VintedClient

logger = logging.getLogger(__name__)

_STOP_WORDS = frozenset({
    "le", "la", "les", "de", "du", "des", "et", "en", "un", "une", "pour", "avec",
    "taille", "size", "homme", "femme", "neuf", "bon", "état", "etat", "très", "tres",
    "the", "and", "new", "used", "vintage", "rare",
})


@dataclass
class MarketPriceAnalysis:
    median_price: float
    avg_price: float
    low_price: float
    high_price: float
    count: int
    margin_eur: float
    margin_percent: float
    discount_vs_market: float
    is_underpriced: bool
    has_real_data: bool
    search_query: str
    sample_titles: list[str]


def _parse_price(item: dict[str, Any]) -> float:
    price = item.get("price") or {}
    return float(price.get("amount", 0))


def _title_tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if len(w) >= 3 and w not in _STOP_WORDS}


def _title_similarity(a: str, b: str) -> float:
    ta, tb = _title_tokens(a), _title_tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _build_search_queries(brand: str, model: str, title: str) -> list[str]:
    queries: list[str] = []
    clean_title = re.sub(r"[^\w\s\-/]", " ", title)
    words = [w for w in clean_title.split() if len(w) >= 3][:6]
    title_q = " ".join(words[:5]).strip()

    if brand and model and model.lower() not in brand.lower():
        queries.append(f"{brand} {model}".strip())
    if brand and title_q:
        queries.append(f"{brand} {title_q}"[:60])
    if title_q and len(title_q) > 8:
        queries.append(title_q[:55])
    if brand:
        queries.append(brand)
    return list(dict.fromkeys(q for q in queries if q))


class VintedMarketPricer:
    """Cherche combien les gens vendent VRAIMENT le même produit sur Vinted."""

    def __init__(self, client: VintedClient) -> None:
        self.client = client
        self._cache: dict[str, list[dict]] = {}

    def _search(self, query: str) -> list[dict]:
        if query in self._cache:
            return self._cache[query]
        try:
            items = self.client.search_catalog(query, per_page=96, order="relevance")
            self._cache[query] = items
            return items
        except Exception as exc:
            logger.warning("Market search failed '%s': %s", query, exc)
            return []

    def analyze(
        self,
        *,
        purchase_price: float,
        brand: str,
        model: str,
        title: str,
        exclude_id: int,
        min_comparables: int = 3,
        min_similarity: float = 0.18,
    ) -> MarketPriceAnalysis:
        empty = MarketPriceAnalysis(
            median_price=0, avg_price=0, low_price=0, high_price=0,
            count=0, margin_eur=0, margin_percent=0, discount_vs_market=0,
            is_underpriced=False, has_real_data=False, search_query="", sample_titles=[],
        )
        if purchase_price <= 0:
            return empty

        queries = _build_search_queries(brand, model, title)
        seen_ids: set[int] = set()
        comparable_prices: list[float] = []
        sample_titles: list[str] = []
        used_query = queries[0] if queries else ""

        for query in queries:
            for item in self._search(query):
                iid = int(item.get("id") or 0)
                if not iid or iid == exclude_id or iid in seen_ids:
                    continue

                item_title = item.get("title") or ""
                item_brand = (item.get("brand_title") or "").lower()
                p = _parse_price(item)
                if p <= 0:
                    continue

                sim = _title_similarity(title, item_title)
                brand_match = (
                    brand.lower() in item_brand
                    or item_brand in brand.lower()
                    or not brand
                )
                if not brand_match and sim < 0.25:
                    continue
                if sim < min_similarity and not brand_match:
                    continue

                seen_ids.add(iid)
                comparable_prices.append(p)
                if len(sample_titles) < 4:
                    sample_titles.append(f"€{p:.0f} — {item_title[:50]}")

        if len(comparable_prices) < min_comparables:
            return MarketPriceAnalysis(
                median_price=0, avg_price=0, low_price=0, high_price=0,
                count=len(comparable_prices), margin_eur=0, margin_percent=0,
                discount_vs_market=0, is_underpriced=False, has_real_data=False,
                search_query=used_query, sample_titles=sample_titles,
            )

        median = statistics.median(comparable_prices)
        avg = statistics.mean(comparable_prices)
        low = min(comparable_prices)
        high = max(comparable_prices)

        discount = ((median - purchase_price) / median * 100) if median > 0 else 0
        margin_eur = median - purchase_price
        margin_pct = (margin_eur / purchase_price * 100) if purchase_price > 0 else 0

        return MarketPriceAnalysis(
            median_price=round(median, 2),
            avg_price=round(avg, 2),
            low_price=round(low, 2),
            high_price=round(high, 2),
            count=len(comparable_prices),
            margin_eur=round(margin_eur, 2),
            margin_percent=round(margin_pct, 1),
            discount_vs_market=round(discount, 1),
            is_underpriced=purchase_price < median * 0.88,
            has_real_data=True,
            search_query=used_query,
            sample_titles=sample_titles,
        )

    def passes_margin_gate(
        self,
        analysis: MarketPriceAnalysis,
        purchase_price: float,
        *,
        min_discount_percent: float = 8.0,
        min_profit_eur: float = 8.0,
        min_profit_after_fees_percent: float = 15.0,
        selling_cost_percent: float = 10.0,
        fixed_cost: float = 2.0,
        condition_mult: float = 1.0,
        conservative_discount: float = 5.0,
    ) -> tuple[bool, float, float, str]:
        if not analysis.has_real_data:
            return False, 0, 0, "pas assez de comparables Vinted"

        median = analysis.median_price
        if purchase_price >= median * 0.95:
            return False, 0, 0, f"prix achat €{purchase_price:.0f} = marché €{median:.0f} — aucune marge"

        if analysis.discount_vs_market < min_discount_percent:
            return False, 0, 0, (
                f"seulement {analysis.discount_vs_market:.0f}% sous le marché "
                f"(€{purchase_price:.0f} vs médiane €{median:.0f})"
            )

        estimated_resale = median * condition_mult * (1 - conservative_discount / 100)
        selling_costs = estimated_resale * (selling_cost_percent / 100)
        net_profit = estimated_resale - selling_costs - fixed_cost - purchase_price
        profit_pct = (net_profit / purchase_price * 100) if purchase_price > 0 else 0

        if net_profit < min_profit_eur:
            return False, estimated_resale, net_profit, (
                f"profit net €{net_profit:.1f} après frais (marché €{median:.0f})"
            )
        if profit_pct < min_profit_after_fees_percent:
            return False, estimated_resale, net_profit, (
                f"marge nette {profit_pct:.0f}% insuffisante"
            )

        return True, round(estimated_resale, 2), round(net_profit, 2), ""
