"""AI services — chat assistant, listing generation, purchase advice."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are ResellPro AI, an expert clothing reselling assistant for Vinted.
You help users find profitable flips, analyze listings, price items, and sell faster.
Be direct, practical, and honest. Warn about risks (fakes, slow movers, bad condition).
Always answer in the user's language. Keep responses concise but actionable."""


class AIService:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._client = None

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _client_or_none(self):
        if not self.api_key:
            return None
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except Exception as exc:
                logger.warning("OpenAI client init failed: %s", exc)
                return None
        return self._client

    def chat(self, message: str, context: dict[str, Any] | None = None) -> str:
        client = self._client_or_none()
        if not client:
            return self._fallback_chat(message, context)

        ctx = ""
        if context:
            ctx = f"\n\nContext:\n{json.dumps(context, ensure_ascii=False, indent=2)}"

        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": message + ctx},
                ],
                max_tokens=800,
                temperature=0.4,
            )
            return resp.choices[0].message.content or ""
        except Exception as exc:
            logger.error("AI chat error: %s", exc)
            return self._fallback_chat(message, context)

    def _fallback_chat(self, message: str, context: dict | None) -> str:
        msg = message.lower()
        if context and "opportunity" in context:
            opp = context["opportunity"]
            if "buy" in msg or "acheter" in msg:
                score = opp.get("score", 0)
                profit = opp.get("potential_profit", 0)
                if score >= 75 and profit >= 15:
                    return (
                        f"Yes — score {score}/100 with €{profit:.0f} estimated profit. "
                        f"Demand: {opp.get('demand_level', 'medium')}. "
                        f"Expected sell time: {opp.get('selling_speed', 'unknown')}. "
                        f"Reason: {opp.get('why_buy', 'solid margin')}."
                    )
                return f"Cautious — score {score}/100. Risk: {opp.get('risk', 'review manually')}."
            if "resell" in msg or "revendre" in msg:
                return f"Estimated resale: €{opp.get('estimated_resale', 0):.0f}. {opp.get('why_buy', '')}"
        return (
            "AI requires an OpenAI API key. Set it in Settings or OPENAI_API_KEY env var. "
            "Basic analysis is still available via the opportunity scores."
        )

    def generate_listing(
        self,
        *,
        brand: str,
        condition: str,
        size: str,
        category: str,
        extra_info: str = "",
        target_price: float = 0,
    ) -> dict[str, str]:
        client = self._client_or_none()
        prompt = (
            f"Generate an optimized Vinted listing in French.\n"
            f"Brand: {brand}\nCondition: {condition}\nSize: {size}\n"
            f"Category: {category}\nInfo: {extra_info}\n"
            f"Target price: €{target_price}\n\n"
            "Return JSON with keys: title, description, keywords (comma-separated), "
            "recommended_price, selling_tips"
        )

        if client:
            try:
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=600,
                    temperature=0.5,
                    response_format={"type": "json_object"},
                )
                return json.loads(resp.choices[0].message.content or "{}")
            except Exception as exc:
                logger.error("Listing generation error: %s", exc)

        return {
            "title": f"{brand} {category} - Taille {size} - {condition}",
            "description": (
                f"✨ {brand} en {condition.lower()}\n"
                f"📏 Taille : {size}\n"
                f"📦 Envoi rapide et soigné\n"
                f"{extra_info}\n"
                f"N'hésitez pas si vous avez des questions !"
            ),
            "keywords": f"{brand}, {category}, {condition}, {size}, vinted, mode",
            "recommended_price": str(target_price or ""),
            "selling_tips": "Ajoutez 4+ photos, publiez le soir, répondez vite aux messages.",
        }

    def optimize_listing(self, title: str, description: str, brand: str) -> dict[str, str]:
        client = self._client_or_none()
        if not client:
            return {
                "title": title,
                "description": description,
                "tips": "Add OpenAI API key for AI optimization.",
            }
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": (
                        f"Optimize this Vinted listing for visibility and sales (French).\n"
                        f"Brand: {brand}\nTitle: {title}\nDescription: {description}\n"
                        "Return JSON: title, description, tips"
                    ),
                }],
                max_tokens=500,
                response_format={"type": "json_object"},
            )
            return json.loads(resp.choices[0].message.content or "{}")
        except Exception as exc:
            logger.error("Optimize error: %s", exc)
            return {"title": title, "description": description, "tips": str(exc)}

    def analyze_purchase(self, opportunity: dict) -> str:
        return self.chat(
            "Should I buy this item? Give a clear yes/no with reasoning.",
            context={"opportunity": opportunity},
        )
