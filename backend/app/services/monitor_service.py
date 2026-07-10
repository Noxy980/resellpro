"""Background opportunity scanner — wraps existing analysis engine."""

from __future__ import annotations

import logging
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

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
            "seen_count": len(self.store._ids),
            "error": self._error,
        }

    def set_callback(self, callback) -> None:
        self._on_opportunity = callback

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("Monitor started")

    def stop(self) -> None:
        self._running = False
        self._status = "stopped"

    def scan_once(self, *, reset_seen: bool = False) -> tuple[list[dict], dict]:
        self._status = "scanning"
        results: list[dict] = []
        candidates: list[ListingAnalysis] = []
        stats = {
            "queries_run": 0,
            "items_fetched": 0,
            "skipped_seen": 0,
            "quick_rejected": 0,
            "analyzed": 0,
            "passed": 0,
            "seen_cleared": 0,
            "errors": 0,
        }

        if reset_seen:
            stats["seen_cleared"] = self.store.clear()
            logger.info("Cleared %d seen listings for fresh scan", stats["seen_cleared"])

        queries = list(dict.fromkeys(
            [b.name for b in self.config.target_brands]
            + self.optimizer.seasonal_search_queries()
        ))
        if self.config.enable_typo_searches:
            queries.extend(self.optimizer.typo_search_queries())
        queries = list(dict.fromkeys(queries))[:24]

        for query in queries:
            stats["queries_run"] += 1
            try:
                items = self.client.search_catalog(query, order="newest_first")
            except Exception as exc:
                logger.error("Search failed for '%s': %s", query, exc)
                self.client.reset_session()
                stats["errors"] += 1
                continue

            stats["items_fetched"] += len(items)
            items = self.optimizer.prioritize(items)
            brand_count = 0

            for item in items:
                lid = item.get("id")
                if not lid:
                    continue
                lid = int(lid)

                if self.store.is_seen(lid):
                    stats["skipped_seen"] += 1
                    continue

                if not self.analyzer.quick_screen(item):
                    stats["quick_rejected"] += 1
                    continue

                if brand_count >= self.config.max_analyses_per_brand:
                    continue
                brand_count += 1

                try:
                    analysis = self.analyzer.analyze(item)
                except Exception as exc:
                    logger.error("Analysis error: %s", exc)
                    stats["errors"] += 1
                    self.store.mark_seen(lid)
                    continue

                stats["analyzed"] += 1
                self.store.mark_seen(lid)

                if analysis:
                    stats["passed"] += 1
                    candidates.append(analysis)

        candidates.sort(key=lambda a: (-a.opportunity_score, -a.potential_profit))
        top = candidates[: self.config.criteria.max_alerts_per_cycle * 3]

        for a in top:
            d = self._to_dict(a)
            results.append(d)
            if self._on_opportunity:
                self._on_opportunity(d)

        self.store.flush()
        self.store.prune()
        self.knowledge_store.flush()
        self._last_scan = datetime.now(timezone.utc)
        self._last_results = results
        self._last_stats = stats
        self._status = "idle"
        self._error = None
        logger.info(
            "Scan done: %d found, %d analyzed, %d passed, %d skipped seen",
            len(results), stats["analyzed"], stats["passed"], stats["skipped_seen"],
        )
        return results, stats

    def _loop(self) -> None:
        while self._running:
            try:
                self.scan_once(reset_seen=False)
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
            "found_at": datetime.now(timezone.utc).isoformat(),
        }

    def analyze_url_or_id(self, vinted_id: int) -> dict | None:
        try:
            items = self.client.search_catalog(str(vinted_id), per_page=5)
            for item in items:
                if int(item.get("id", 0)) == vinted_id:
                    analysis = self.analyzer.analyze(item)
                    return self._to_dict(analysis) if analysis else None
        except Exception as exc:
            logger.error("Manual analyze error: %s", exc)
        return None


monitor = MonitorService()
