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

RÈGLES DE FORMATAGE (obligatoire):
- Utilise le Markdown pour structurer tes réponses
- **Gras** pour les points clés et chiffres importants
- ## Titres pour les sections
- Listes à puces pour les recommandations
- Tableaux si tu compares des options
- Sois direct, pratique et honnête
- Signale les risques (contrefaçons, articles lents, mauvais état)
- Réponds dans la langue de l'utilisateur (français par défaut)
- Réponses actionnables avec des chiffres concrets (€, %, jours)"""


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
        color: str = "", defects: str = "", purchase_price: float = 0,
    ) -> dict[str, str]:
        from datetime import date
        month = date.today().month
        season = "été" if month in (6, 7, 8) else "hiver" if month in (12, 1, 2) else "mi-saison"

        prompt = f"""Génère une annonce Vinted professionnelle en français pour un revendeur expert.

ARTICLE:
- Marque: {brand}
- Catégorie: {category}
- Taille: {size}
- Couleur: {color or 'non précisée'}
- État: {condition}
- Défauts: {defects or 'aucun'}
- Prix d'achat: €{purchase_price or 'N/A'}
- Prix cible revente: €{target_price or 'à estimer'}
- Saison actuelle: {season}
- Détails: {extra_info}

Réponds UNIQUEMENT en JSON valide:
{{
  "title": "titre optimisé Vinted max 80 caractères avec mots-clés recherche",
  "description": "description professionnelle 150-300 mots avec emojis discrets, détails, mesures si pertinent, rassurante",
  "keywords": "mots-clés séparés par virgules",
  "recommended_price": "prix idéal en nombre",
  "min_price": "prix minimum acceptable",
  "estimated_margin": "marge estimée en €",
  "selling_tips": "conseils: timing publication, photos, négociation",
  "photo_tips": "conseils photo spécifiques à cet article",
  "category": "{category}"
}}"""
        result = self._request([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ], model=MODEL_STRUCTURED, json_mode=True, max_tokens=1200)

        parsed = self._parse_json(result)
        if parsed:
            return parsed

        return {
            "title": f"{brand} {category} {color} — Taille {size} — {condition}".strip(),
            "description": (
                f"✨ {brand} en excellent état\n"
                f"📏 Taille {size}\n"
                f"🎨 Couleur: {color or 'voir photos'}\n"
                f"📦 Envoi rapide et soigné\n"
                f"{defects and '⚠️ ' + defects or ''}\n{extra_info}"
            ).strip(),
            "keywords": f"{brand}, {category}, {size}, {color}, vinted, mode",
            "recommended_price": str(target_price or ""),
            "min_price": str(max(0, (target_price or 0) * 0.85)),
            "estimated_margin": str(max(0, (target_price or 0) - (purchase_price or 0))),
            "selling_tips": "Publier entre 19h-22h, 4+ photos, répondre en moins de 2h.",
            "photo_tips": "Lumière naturelle, fond neutre, montrer étiquette et défauts.",
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
