"""Image and listing photo analysis — model hints, defects, authenticity signals."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ImageAssessment:
    score: float  # 0-100 listing quality
    photo_count: int
    detected_model: str | None
    has_defect_signals: bool
    is_rare_piece: bool
    authenticity_risk: str  # low / medium / high
    photo_quality: str  # poor / average / good
    ai_analysis: str | None


class ImageAnalyzer:
    def __init__(self, rare_models: list[str], defect_keywords: list[str]) -> None:
        self.rare_models = [r.lower() for r in rare_models]
        self.defect_keywords = [d.lower() for d in defect_keywords]
        self._openai_key = os.environ.get("OPENAI_API_KEY", "")

    def _extract_photo_meta(self, item: dict[str, Any]) -> tuple[int, int, str | None]:
        photos = item.get("photos") or []
        if not photos and item.get("photo"):
            photos = [item["photo"]]
        count = len(photos)
        max_res = 0
        dominant = None
        for p in photos:
            w = int(p.get("width") or 0)
            h = int(p.get("height") or 0)
            max_res = max(max_res, max(w, h))
            if not dominant:
                dominant = p.get("dominant_color")
        return count, max_res, dominant

    def _detect_model_from_title(self, title: str, brand: str, hot_canonical: str | None) -> str | None:
        if hot_canonical:
            return hot_canonical
        cleaned = title
        if brand:
            cleaned = cleaned.replace(brand, "").strip()
        return cleaned[:60] if cleaned else None

    def _authenticity_risk(self, title: str, brand: str, has_red_flags: bool) -> str:
        text = title.lower()
        high_risk = ["fake", "replica", "réplique", "replique", "copy", "inspired", "style", "dupe"]
        medium_risk = ["sans étiquette", "sans etiquette", "no tag", "unbranded"]
        if has_red_flags or any(r in text for r in high_risk):
            return "high"
        premium = ["stone island", "supreme", "arc'teryx", "moncler", "canada goose"]
        if any(p in f"{brand} {text}".lower() for p in premium):
            if any(r in text for r in medium_risk):
                return "medium"
        return "low"

    def _try_ai_analysis(self, image_url: str | None, title: str) -> str | None:
        if not self._openai_key or not image_url:
            return None
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self._openai_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": (
                            f"Analyze this clothing listing photo for resale. Title: {title}. "
                            "Reply in 2 short sentences: visible condition/defects, and resale appeal."
                        )},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }],
                max_tokens=120,
            )
            return response.choices[0].message.content
        except Exception as exc:
            logger.debug("AI image analysis unavailable: %s", exc)
            return None

    def assess(
        self,
        item: dict[str, Any],
        *,
        title: str,
        brand: str,
        hot_canonical: str | None,
        has_red_flags: bool,
    ) -> ImageAssessment:
        photo_count, max_res, dominant = self._extract_photo_meta(item)
        text = f"{title}".lower()

        has_defects = any(kw in text for kw in self.defect_keywords)
        is_rare = any(r in text for r in self.rare_models)

        if photo_count >= 4 and max_res >= 600:
            photo_quality = "good"
            quality_score = 90
        elif photo_count >= 2 and max_res >= 400:
            photo_quality = "average"
            quality_score = 65
        else:
            photo_quality = "poor"
            quality_score = 35

        if has_defects:
            quality_score -= 25
        if is_rare:
            quality_score += 10

        auth_risk = self._authenticity_risk(title, brand, has_red_flags)
        if auth_risk == "high":
            quality_score -= 40
        elif auth_risk == "medium":
            quality_score -= 15

        image_url = None
        photos = item.get("photos") or []
        if photos:
            image_url = photos[0].get("url")
        elif item.get("photo"):
            image_url = item["photo"].get("url")

        ai_note = self._try_ai_analysis(image_url, title)

        return ImageAssessment(
            score=round(min(100, max(0, quality_score)), 1),
            photo_count=photo_count,
            detected_model=self._detect_model_from_title(title, brand, hot_canonical),
            has_defect_signals=has_defects,
            is_rare_piece=is_rare,
            authenticity_risk=auth_risk,
            photo_quality=photo_quality,
            ai_analysis=ai_note,
        )
