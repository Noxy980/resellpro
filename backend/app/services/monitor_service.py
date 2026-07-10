"""Background opportunity scanner — Gem Hunter mode for maximum pépites."""

from __future__ import annotations

import logging
import random
import sys
import threading
import time
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.brand_intelligence import get_fast_mover_brands, get_seasonal_search_terms
from src.gem_hunter import build_gem_queries, is_pepite_listing
from src.seasonal import get_current_season
from src.analyzer import ListingAnalysis, ListingAnalyzer  # noqa: E402
from src.config import load_config, resolve_path  # noqa: E402
from src.knowledge_base import KnowledgeBaseStore  # noqa: E402
from src.search_optimizer import SearchOptimizer  # noqa: E402
from src.storage import SeenListingsStore  # noqa: E402
from src.vinted_client import VintedClient  # noqa: E402

logger = logging.getLogger(__name__)


class MonitorService:
    def __init__(self) -> None:
        self.config = load_config()
        self._running = False
        self._thread: threading.Thread | None = None
        self._last_scan: datetime | None = None
        self._last_results: list[dict] = []
        self._last_stats: dict = {}
        self._status = "idle"
        self._error: str | None = None
        self._on_opportunity = None

        self.store = SeenListingsStore(resolve_path(self.config.seen_listings_file))
        self.knowledge_store = KnowledgeBaseStore(resolve_path(self.config.knowledge_base_file))
        self.client = VintedClient(self.config)
        self.analyzer = ListingAnalyzer(self.config, self.client, self.knowledge_store)
        self.optimizer = SearchOptimizer(self.config)

    @property
    def status(self) -> dict:
        return {
            "running": self._running,
            "status": self._status,
            "last_scan": self._last_scan.isoformat() if self._last_scan else None,
            "last_count": len(self._last_results),
            "last_stats": self._last_stats,
            "vinted_error": self.client.last_error,
            "error": self._error,
            "mode": "gem_hunter",
        }

    def set_callback(self, callback) -> None:
        self._on_opportunity = callback

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("Monitor started (gem hunter)")

    def stop(self) -> None:
        self._running = False
        self._status = "stopped"

    def _empty_stats(self) -> dict:
        return {
            "queries_run": 0,
            "items_fetched": 0,
            "analyzed": 0,
            "passed": 0,
            "errors": 0,
            "error_samples": [],
            "pepites_found": 0,
        }

    def _build_queries(self) -> list[str]:
        """80+ requêtes — maillots, hype, clubs, saison."""
        season = get_current_season()
        queries: list[str] = []

        queries.extend(build_gem_queries(season))
        queries.extend(get_seasonal_search_terms(season)[:12])

        for brand in get_fast_mover_brands(season)[:12]:
            queries.append(brand)

        for b in self.config.target_brands:
            queries.append(b.name)

        if self.config.enable_typo_searches:
            queries.extend(self.optimizer.typo_search_queries())
        queries.extend(self.optimizer.seasonal_search_queries())

        unique = list(dict.fromkeys(queries))
        random.shuffle(unique)
        return unique[:80]

    def _run_query(self, query: str, stats: dict) -> list[ListingAnalysis]:
        found: list[ListingAnalysis] = []
        stats["queries_run"] += 1
        per_page = self.config.listings_per_search

        try:
            items = self.client.search_catalog(
                query,
                order="newest_first",
                per_page=per_page,
            )
        except Exception as exc:
            err = f"{query}: {exc}"
            logger.error("Search failed: %s", err)
            stats["errors"] += 1
            if len(stats["error_samples"]) < 3:
                stats["error_samples"].append(err[:200])
            self.client.reset_session(rotate=True)
            return found

        stats["items_fetched"] += len(items)
        if not items:
            return found

        items = self.optimizer.prioritize(items)
        max_analyze = self.config.max_analyses_per_brand
        analyzed_this_query = 0

        for item in items:
            if analyzed_this_query >= max_analyze:
                break
            if not self.analyzer.quick_screen(item):
                continue

            analyzed_this_query += 1
            try:
                analysis = self.analyzer.analyze(item, gem_hunt=True)
            except Exception as exc:
                logger.error("Analysis error: %s", exc)
                stats["errors"] += 1
                continue

            stats["analyzed"] += 1
            if analysis:
                stats["passed"] += 1
                title = item.get("title") or ""
                brand = item.get("brand_title") or ""
                fav = int(item.get("favourite_count") or 0)
                if is_pepite_listing(title, brand, fav):
                    stats["pepites_found"] = stats.get("pepites_found", 0) + 1
                found.append(analysis)

        return found

    def scan_once(self, *, reset_seen: bool = False) -> tuple[list[dict], dict]:
        self._status = "scanning"
        results: list[dict] = []
        candidates: list[ListingAnalysis] = []
        stats = self._empty_stats()

        if reset_seen:
            stats["seen_cleared"] = self.store.clear()

        for query in self._build_queries():
            candidates.extend(self._run_query(query, stats))

        candidates.sort(key=lambda a: (-a.opportunity_score, -a.potential_profit))
        top = candidates[: max(self.config.criteria.max_alerts_per_cycle, 25)]

        for a in top:
            d = self._to_dict(a)
            results.append(d)
            if self._on_opportunity:
                self._on_opportunity(d)

        self.knowledge_store.flush()
        self._last_scan = datetime.now(timezone.utc)
        self._last_results = results
        self._last_stats = stats
        self._status = "idle"
        self._error = stats["error_samples"][0] if stats["error_samples"] and not results else None
        logger.info(
            "Gem scan: %d results (%d pepites), %d fetched, %d analyzed",
            len(results), stats.get("pepites_found", 0), stats["items_fetched"], stats["analyzed"],
        )
        return results, stats

    def scan_stream(
        self,
        duration_minutes: int = 15,
        *,
        reset_seen: bool = False,
    ) -> Iterator[dict]:
        self._status = "scanning"
        stats = self._empty_stats()
        start = time.monotonic()
        deadline = start + max(1, duration_minutes) * 60
        yielded_ids: set[int] = set()
        queries = self._build_queries()
        query_idx = 0

        if reset_seen:
            stats["seen_cleared"] = self.store.clear()

        yield {
            "event": "start",
            "duration_minutes": duration_minutes,
            "queries_total": len(queries),
            "mode": "gem_hunter",
        }

        try:
            while time.monotonic() < deadline:
                query = queries[query_idx % len(queries)]
                query_idx += 1

                yield {
                    "event": "progress",
                    "query": query,
                    "elapsed_seconds": int(time.monotonic() - start),
                    "remaining_seconds": int(max(0, deadline - time.monotonic())),
                    "queries_run": stats["queries_run"],
                    "items_fetched": stats["items_fetched"],
                    "analyzed": stats["analyzed"],
                    "passed": stats["passed"],
                    "errors": stats["errors"],
                    "pepites_found": stats.get("pepites_found", 0),
                }

                for analysis in self._run_query(query, stats):
                    d = self._to_dict(analysis)
                    vid = int(d.get("vinted_id") or 0)
                    if vid and vid not in yielded_ids:
                        yielded_ids.add(vid)
                        yield {"event": "found", "opportunity": d}

                time.sleep(0.15)
        finally:
            self.knowledge_store.flush()
            self._last_scan = datetime.now(timezone.utc)
            self._last_stats = {**stats, "found_count": len(yielded_ids)}
            self._status = "idle"
            self._error = (
                stats["error_samples"][0]
                if stats["error_samples"] and not yielded_ids
                else None
            )
            yield {
                "event": "done",
                "stats": self._last_stats,
                "found_count": len(yielded_ids),
            }

    def _loop(self) -> None:
        while self._running:
            try:
                self.scan_once()
            except Exception as exc:
                self._error = str(exc)
                self._status = "error"
                logger.error("Monitor loop error: %s", exc)
            for _ in range(self.config.poll_interval_seconds):
                if not self._running:
                    break
                time.sleep(1)

    @staticmethod
    def _to_dict(a: ListingAnalysis) -> dict:
        return {
            "vinted_id": a.listing_id,
            "title": a.title,
            "brand": a.brand,
            "model": a.model,
            "category": a.category,
            "size": a.size,
            "condition": a.condition,
            "price": a.price,
            "estimated_resale": a.estimated_resale_value,
            "potential_profit": a.potential_profit,
            "profit_percent": a.profit_percent,
            "score": a.opportunity_score,
            "demand_level": a.demand_level,
            "selling_speed": a.selling_speed,
            "quick_sale_probability": a.quick_sale_probability,
            "why_buy": a.why_buy,
            "risk": a.risk,
            "url": a.url,
            "image_url": a.image_url,
            "score_breakdown": a.score_breakdown,
            "ease_of_resale": a.ease_of_resale,
            "is_underpriced": a.is_underpriced,
            "comparable_median": a.comparable_median,
            "comparable_count": a.comparable_count,
            "found_at": datetime.now(timezone.utc).isoformat(),
        }

    def analyze_url_or_id(self, vinted_id: int) -> dict | None:
        try:
            items = self.client.search_catalog(str(vinted_id), per_page=5)
            for item in items:
                if int(item.get("id", 0)) == vinted_id:
                    analysis = self.analyzer.analyze(item, gem_hunt=True)
                    return self._to_dict(analysis) if analysis else None
        except Exception as exc:
            logger.error("Manual analyze error: %s", exc)
        return None


monitor = MonitorService()
