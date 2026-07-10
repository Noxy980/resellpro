#!/usr/bin/env python3
"""
Vinted Resale Assistant — expert-grade buy-and-resell monitor.

Usage:
    python main.py              # Run continuously
    python main.py --once       # Single scan cycle
    python main.py --dry-run    # Analyze without Discord alerts
"""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import time
from datetime import datetime

from src.analyzer import ListingAnalyzer
from src.config import load_config, resolve_path
from src.discord_notifier import DiscordNotifier
from src.knowledge_base import KnowledgeBaseStore
from src.search_optimizer import SearchOptimizer
from src.storage import SeenListingsStore
from src.vinted_client import VintedClient

logger = logging.getLogger("vinted_assistant")
_running = True


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger("curl_cffi").setLevel(logging.WARNING)


def _handle_signal(signum: int, frame: object) -> None:
    global _running
    logger.info("Shutdown requested, finishing current cycle...")
    _running = False


def _build_search_queries(config, optimizer: SearchOptimizer) -> list[str]:
    queries = list(dict.fromkeys(
        [b.name for b in config.target_brands] + optimizer.seasonal_search_queries()
    ))
    if config.enable_typo_searches:
        queries.extend(optimizer.typo_search_queries())
    return list(dict.fromkeys(queries))[:24]


def run_scan_cycle(
    config,
    client: VintedClient,
    analyzer: ListingAnalyzer,
    optimizer: SearchOptimizer,
    store: SeenListingsStore,
    knowledge_store: KnowledgeBaseStore,
    notifier: DiscordNotifier | None,
    *,
    dry_run: bool = False,
) -> int:
    alerts_sent = 0
    new_seen = 0
    analyzed = 0
    candidates: list = []

    queries = _build_search_queries(config, optimizer)

    for query in queries:
        if not _running:
            break

        logger.info("Searching: %s", query)

        try:
            items = client.search_catalog(query, order="newest_first")
        except Exception as exc:
            logger.error("Search failed for '%s': %s", query, exc)
            client.reset_session()
            continue

        items = optimizer.prioritize(items)
        brand_analyses = 0

        for item in items:
            if not _running:
                break

            listing_id = item.get("id")
            if not listing_id:
                continue
            listing_id = int(listing_id)

            if store.is_seen(listing_id):
                continue

            store.mark_seen(listing_id)
            new_seen += 1

            if not analyzer.quick_screen(item):
                continue

            if brand_analyses >= config.max_analyses_per_brand:
                continue

            brand_analyses += 1
            analyzed += 1

            try:
                analysis = analyzer.analyze(item)
            except Exception as exc:
                logger.error("Analysis failed for %d: %s", listing_id, exc)
                continue

            if analysis is None:
                continue

            logger.info(
                "EXPERT PICK [%d] %s — €%.0f → €%.0f | profit €%.0f | %s | demand %s",
                analysis.opportunity_score,
                analysis.title[:60],
                analysis.price,
                analysis.estimated_resale_value,
                analysis.potential_profit,
                analysis.selling_speed,
                analysis.demand_level,
            )
            logger.info("  Why: %s", analysis.why_buy)
            logger.info("  Risk: %s", analysis.risk)

            candidates.append(analysis)

    candidates.sort(key=lambda a: (-a.opportunity_score, -a.potential_profit, a.estimated_days_to_sell))
    top = candidates[: config.criteria.max_alerts_per_cycle]

    for analysis in top:
        if dry_run:
            alerts_sent += 1
            continue
        if notifier and notifier.send_opportunity(analysis):
            alerts_sent += 1

    if len(candidates) > len(top):
        logger.info(
            "Held back %d good listings — only top %d sent (quality over quantity)",
            len(candidates) - len(top), len(top),
        )

    store.prune()
    store.flush()
    knowledge_store.flush()
    logger.info(
        "Cycle done — %d new listings seen, %d deep-analyzed, %d expert alerts",
        new_seen, analyzed, alerts_sent,
    )
    return alerts_sent


def main() -> int:
    parser = argparse.ArgumentParser(description="Vinted Resale Assistant — Expert Mode")
    parser.add_argument("--once", action="store_true", help="Single scan cycle")
    parser.add_argument("--dry-run", action="store_true", help="No Discord alerts")
    parser.add_argument("--verbose", "-v", action="store_true", help="Debug logging")
    parser.add_argument("--config", type=str, default=None, help="Config path")
    args = parser.parse_args()

    _setup_logging(args.verbose)

    try:
        config = load_config(args.config)
    except FileNotFoundError:
        logger.error("config.yaml not found")
        return 1
    except Exception as exc:
        logger.error("Config error: %s", exc)
        return 1

    if not config.target_brands:
        logger.error("No target brands configured")
        return 1

    store = SeenListingsStore(resolve_path(config.seen_listings_file))
    knowledge_store = KnowledgeBaseStore(resolve_path(config.knowledge_base_file))
    client = VintedClient(config)
    analyzer = ListingAnalyzer(config, client, knowledge_store)
    optimizer = SearchOptimizer(config)
    notifier = DiscordNotifier(config.discord_webhook_url) if config.discord_webhook_url else None

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    logger.info("Vinted Expert Resale Assistant started")
    logger.info("Brands: %d | Hot models: %d | Min score: %d | Max days to sell: %d",
                len(config.target_brands), len(config.hot_models),
                config.criteria.min_opportunity_score, config.criteria.max_days_to_sell)

    if args.dry_run:
        logger.info("DRY RUN — no Discord alerts")

    try:
        while _running:
            logger.info("--- Scan at %s ---", datetime.now().strftime("%H:%M:%S"))
            try:
                run_scan_cycle(
                    config, client, analyzer, optimizer, store,
                    knowledge_store, notifier, dry_run=args.dry_run,
                )
            except Exception as exc:
                logger.error("Cycle error: %s", exc)
                client.reset_session()

            if args.once:
                break
            if not _running:
                break

            logger.info("Next scan in %ds...", config.poll_interval_seconds)
            for _ in range(config.poll_interval_seconds):
                if not _running:
                    break
                time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        store.flush()
        knowledge_store.flush()
        logger.info("Stopped.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
