"""OpenRouter AI — free models only, integrated reseller assistant."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)

OPENROUTER_BASE = "https://openrouter.ai/api/v1"

# Free models only
MODEL_CHAT = "openrouter/free"
MODEL_STRUCTURED = "meta-llama/llama-3.3-70b-instruct:free"
MODEL_VISION = "google/gemma-4-31b-it:free"

SYSTEM_PROMPT = """Tu es ResellPro AI, assistant expert en achat-revente de vêtements sur Vinted.
Tu aides à trouver des opportunités rentables, analyser des articles, fixer les prix et vendre plus vite.
Sois direct, pratique et honnête. Signale les risques (contrefaçons, articles lents, mauvais état).
Réponds dans la langue de l'utilisateur. Réponses concises et actionnables."""


class OpenRouterAI:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = (
            api_key
            or os.environ.get("OPENROUTER_API_KEY", "")
            or os.environ.get("OPENAI_API_KEY", "")
        )

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _request(
        self,
        messages: list[dict],
        *,
        model: str = MODEL_CHAT,
        max_tokens: int = 900,
        temperature: float = 0.4,
        json_mode: bool = False,
    ) -> str:
        if not self.api_key:
            return ""

        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}

        try:
            with httpx.Client(timeout=60) as client:
                resp = client.post(
                    f"{OPENROUTER_BASE}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://resellpro.local",
                        "X-Title": "ResellPro",
                    },
                    json=body,
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"] or ""
        except Exception as exc:
            logger.error("OpenRouter error (%s): %s", model, exc)
            return ""

    def chat(self, message: str, context: dict[str, Any] | None = None) -> str:
        ctx = ""
        if context:
            ctx = f"\n\nContexte:\n{json.dumps(context, ensure_ascii=False, indent=2)}"

        result = self._request([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message + ctx},
        ])
        if result:
            return result
        return self._fallback(message, context)

    def _fallback(self, message: str, context: dict | None) -> str:
        msg = message.lower()
        if context and "opportunity" in context:
            opp = context["opportunity"]
            if any(w in msg for w in ("acheter", "buy", "affaire", "bon")):
                s, p = opp.get("score", 0), opp.get("potential_profit", 0)
                if s >= 75 and p >= 15:
                    return f"Oui — score {s}/100, profit estimé €{p:.0f}. {opp.get('why_buy', '')}"
                return f"Prudence — score {s}/100. Risque: {opp.get('risk', '')}"
        return "Configurez votre clé OpenRouter dans Paramètres pour activer l'IA complète."

    def _parse_json(self, text: str) -> dict:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
        return {}

    def generate_listing(
        self, *, brand: str, condition: str, size: str,
        category: str, extra_info: str = "", target_price: float = 0,
    ) -> dict[str, str]:
        prompt = (
            f"Génère une annonce Vinted optimisée en français.\n"
            f"Marque: {brand}\nÉtat: {condition}\nTaille: {size}\n"
            f"Catégorie: {category}\nDétails: {extra_info}\nPrix cible: €{target_price}\n\n"
            'Réponds en JSON: {"title","description","keywords","recommended_price","selling_tips","category"}'
        )
        result = self._request([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ], model=MODEL_STRUCTURED, json_mode=True, max_tokens=700)

        parsed = self._parse_json(result)
        if parsed:
            return parsed

        return {
            "title": f"{brand} {category} — Taille {size} — {condition}",
            "description": f"✨ {brand} en {condition}\n📏 Taille {size}\n📦 Envoi rapide\n{extra_info}",
            "keywords": f"{brand}, {category}, {size}, vinted",
            "recommended_price": str(target_price or ""),
            "selling_tips": "4+ photos, publier le soir, répondre vite.",
            "category": category,
        }

    def optimize_listing(self, title: str, description: str, brand: str) -> dict[str, str]:
        result = self._request([{
            "role": "user",
            "content": (
                f"Optimise cette annonce Vinted (français). Marque: {brand}\n"
                f"Titre: {title}\nDescription: {description}\n"
                'JSON: {"title","description","tips","keywords"}'
            ),
        }], model=MODEL_STRUCTURED, json_mode=True)
        return self._parse_json(result) or {"title": title, "description": description, "tips": ""}

    def analyze_opportunity(self, opp: dict) -> str:
        return self.chat(
            "Analyse cette opportunité. Dois-je acheter ? Prix de revente réaliste ? Risques ?",
            context={"opportunity": opp},
        )

    def recommend_price(self, brand: str, model: str, condition: str, category: str) -> str:
        return self.chat(
            f"Quel prix dois-je mettre pour revendre un {brand} {model} "
            f"({category}, {condition}) sur Vinted ? Donne un prix précis en € avec justification."
        )

    def selling_strategy(self, brand: str, model: str) -> str:
        return self.chat(
            f"Comment vendre rapidement un {brand} {model} sur Vinted ? "
            "Stratégie concrète: titre, photos, prix, timing."
        )

    def trend_analysis(self) -> str:
        return self.chat(
            "Quels vêtements et marques se revendent le mieux sur Vinted en ce moment ? "
            "Top 5 opportunités pour un revendeur."
        )

    def analyze_photo(self, image_url: str, title: str = "") -> str:
        result = self._request([
            {"role": "system", "content": "Analyse cette photo de vêtement pour la revente Vinted."},
            {"role": "user", "content": [
                {"type": "text", "text": f"Analyse cette photo pour revente. Article: {title}. État, attrait, conseils."},
                {"type": "image_url", "image_url": {"url": image_url}},
            ]},
        ], model=MODEL_VISION, max_tokens=400)
        return result or "Analyse photo indisponible."
