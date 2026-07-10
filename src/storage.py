"""Persistent storage for already-processed listing IDs."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


class SeenListingsStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._ids: set[int] = set()
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._save()
            return

        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
            self._ids = {int(x) for x in data.get("seen_ids", [])}
            logger.info("Loaded %d previously seen listings", len(self._ids))
        except (json.JSONDecodeError, OSError, ValueError) as exc:
            logger.warning("Could not load seen listings (%s), starting fresh", exc)
            self._ids = set()

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "seen_ids": sorted(self._ids),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def is_seen(self, listing_id: int) -> bool:
        return listing_id in self._ids

    def mark_seen(self, listing_id: int) -> None:
        self._ids.add(listing_id)

    def mark_many(self, listing_ids: list[int]) -> None:
        self._ids.update(listing_ids)

    def clear(self) -> int:
        count = len(self._ids)
        self._ids = set()
        self._save()
        return count

    def flush(self) -> None:
        self._save()

    def prune(self, max_entries: int = 50_000) -> None:
        """Keep storage bounded by dropping oldest IDs when over limit."""
        if len(self._ids) <= max_entries:
            return
        trimmed = set(sorted(self._ids)[-max_entries:])
        removed = len(self._ids) - len(trimmed)
        self._ids = trimmed
        logger.info("Pruned %d old seen listing IDs", removed)
