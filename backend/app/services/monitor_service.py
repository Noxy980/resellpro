"""Background opportunity scanner — wraps existing analysis engine."""

from __future__ import annotations

import logging
import sys
import threading
import time
from collections.abc import Iterator
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
            "vinted_error": self.client.last_error,
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

    def _empty_stats(self) -> dict:
        return {
            "queries_run": 0,
            "items_fetched": 0,
            "analyzed": 0,
            "passed": 0,
            "errors": 0,
            "error_samples": [],
        }

    def _build_queries(self) -> list[str]:
        queries = [b.name for b in self.config.target_brands]
        if self.config.enable_typo_searches:
            queries.extend(self.optimizer.typo_search_queries()[:6])
        queries.extend(self.optimizer.seasonal_search_queries()[:8])
        return list(dict.fromkeys(queries))[:16]

    def _run_query(self, query: str, stats: dict) -> list[ListingAnalysis]:
        """Run one catalog search and return analyses that pass the scorer."""
        found: list[ListingAnalysis] = []
        stats["queries_run"] += 1
        try:
            items = self.client.search_catalog(query, order="newest_first", per_page=32)
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
        analyzed_this_query = 0

        for item in items:
            if analyzed_this_query >= 8:
                break
            if not self.analyzer.quick_screen(item):
                continue

            analyzed_this_query += 1
            try:
                analysis = self.analyzer.analyze(item, relaxed=True)
            except Exception as exc:
                logger.error("Analysis error: %s", exc)
                stats["errors"] += 1
                continue

            stats["analyzed"] += 1
            if analysis:
                stats["passed"] += 1
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
        top = candidates[: max(self.config.criteria.max_alerts_per_cycle * 2, 10)]

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
            "Scan: %d results, %d fetched, %d analyzed, %d errors",
            len(results), stats["items_fetched"], stats["analyzed"], stats["errors"],
        )
        return results, stats

    def scan_stream(
        self,
        duration_minutes: int = 15,
        *,
        reset_seen: bool = False,
    ) -> Iterator[dict]:
        """Yield SSE event dicts while scanning for the given duration."""
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
                }

                for analysis in self._run_query(query, stats):
                    d = self._to_dict(analysis)
                    vid = int(d.get("vinted_id") or 0)
                    if vid and vid not in yielded_ids:
                        yielded_ids.add(vid)
                        yield {"event": "found", "opportunity": d}

                time.sleep(0.25)
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
            "found_at": datetime.now(timezone.utc).isoformat(),
        }

    def analyze_url_or_id(self, vinted_id: int) -> dict | None:
        try:
            items = self.client.search_catalog(str(vinted_id), per_page=5)
            for item in items:
                if int(item.get("id", 0)) == vinted_id:
                    analysis = self.analyzer.analyze(item, relaxed=True)
                    return self._to_dict(analysis) if analysis else None
        except Exception as exc:
            logger.error("Manual analyze error: %s", exc)
        return None


monitor = MonitorService()
