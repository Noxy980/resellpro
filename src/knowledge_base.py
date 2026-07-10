"""Knowledge base — learns which models resell well over time."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ModelRecord:
    brand: str
    model_key: str
    samples: int = 0
    avg_purchase_price: float = 0.0
    avg_resale_price: float = 0.0
    avg_profit: float = 0.0
    avg_days_to_sell: float = 30.0
    success_rate: float = 0.5
    last_updated: str = ""

    def update(
        self,
        purchase_price: float,
        resale_price: float,
        profit: float,
        days_to_sell: float,
    ) -> None:
        n = self.samples
        self.samples = n + 1
        self.avg_purchase_price = (self.avg_purchase_price * n + purchase_price) / self.samples
        self.avg_resale_price = (self.avg_resale_price * n + resale_price) / self.samples
        self.avg_profit = (self.avg_profit * n + profit) / self.samples
        self.avg_days_to_sell = (self.avg_days_to_sell * n + days_to_sell) / self.samples
        if profit > 0:
            self.success_rate = (self.success_rate * n + 1.0) / self.samples
        else:
            self.success_rate = (self.success_rate * n) / self.samples
        self.last_updated = datetime.now(timezone.utc).isoformat()


@dataclass
class KnowledgeBase:
    models: dict[str, ModelRecord] = field(default_factory=dict)

    @staticmethod
    def model_key(brand: str, model: str) -> str:
        return f"{brand.lower().strip()}|{model.lower().strip()}"

    def get(self, brand: str, model: str) -> ModelRecord | None:
        return self.models.get(self.model_key(brand, model))

    def learn(
        self,
        brand: str,
        model: str,
        purchase_price: float,
        resale_price: float,
        profit: float,
        days_to_sell: float,
    ) -> ModelRecord:
        key = self.model_key(brand, model)
        record = self.models.get(key)
        if not record:
            record = ModelRecord(brand=brand, model_key=model.lower().strip())
            self.models[key] = record
        record.update(purchase_price, resale_price, profit, days_to_sell)
        return record

    def suggested_buy_price(self, brand: str, model: str) -> float | None:
        record = self.get(brand, model)
        if record and record.samples >= 2:
            return round(record.avg_purchase_price * 1.1, 2)
        return None

    def expected_resale(self, brand: str, model: str) -> float | None:
        record = self.get(brand, model)
        if record and record.samples >= 2:
            return round(record.avg_resale_price, 2)
        return None

    def expected_days(self, brand: str, model: str) -> float | None:
        record = self.get(brand, model)
        if record and record.samples >= 2:
            return record.avg_days_to_sell
        return None


class KnowledgeBaseStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.kb = KnowledgeBase()
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._save()
            return
        try:
            with open(self.path, encoding="utf-8") as f:
                raw = json.load(f)
            for key, data in raw.get("models", {}).items():
                self.kb.models[key] = ModelRecord(**data)
            logger.info("Knowledge base loaded — %d models tracked", len(self.kb.models))
        except (json.JSONDecodeError, OSError, TypeError) as exc:
            logger.warning("Could not load knowledge base (%s)", exc)

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "models": {k: asdict(v) for k, v in self.kb.models.items()},
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def flush(self) -> None:
        self._save()
