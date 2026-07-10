"""Aesthetic and style analysis — trend fit, colors, sellability."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .config import AppConfig


@dataclass
class AestheticAssessment:
    score: float  # 0-100
    trend_match: str | None
    color_appeal: float
    style_tags: list[str]
    is_dated: bool
    is_hard_to_sell: bool
    is_kids_item: bool
    photo_attractiveness: float


class AestheticAnalyzer:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._trending = [t.lower() for t in config.trending_styles]
        self._dated = [d.lower() for d in config.dated_styles]
        self._appealing_colors = [c.lower() for c in config.appealing_colors]
        self._hard_to_sell = [h.lower() for h in config.hard_to_sell_signals]

    def _extract_colors(self, title: str, dominant_color: str | None) -> list[str]:
        colors = []
        color_words = [
            "noir", "black", "blanc", "white", "bleu", "blue", "navy", "gris", "grey", "gray",
            "beige", "camel", "marron", "brown", "vert", "green", "rouge", "red", "rose", "pink",
            "orange", "yellow", "jaune", "cream", "crème", "olive", "khaki", "bordeaux",
        ]
        text = title.lower()
        for c in color_words:
            if c in text:
                colors.append(c)
        if dominant_color:
            colors.append(dominant_color.lower())
        return colors

    def _color_appeal(self, colors: list[str]) -> float:
        if not colors:
            return 55.0
        appealing = {"noir", "black", "navy", "bleu", "blue", "blanc", "white", "beige",
                     "camel", "gris", "grey", "gray", "cream", "crème", "olive", "khaki", "bordeaux"}
        score = 50.0
        for c in colors:
            if c in appealing or any(a in c for a in self.config.appealing_colors):
                score += 12
            if c in ("rose", "pink", "orange", "yellow", "jaune"):
                score -= 5
        return min(100, max(0, score))

    def assess(
        self,
        *,
        title: str,
        category: str,
        photo_count: int,
        dominant_color: str | None,
        photo_resolution: int,
    ) -> AestheticAssessment:
        text = title.lower()
        style_tags: list[str] = []
        trend_match: str | None = None
        trend_score = 40.0

        for trend in self.config.trending_styles:
            if trend.lower() in text:
                style_tags.append(trend)
                trend_match = trend
                trend_score += 15

        is_dated = any(d in text for d in self._dated)
        if is_dated:
            trend_score -= 25

        is_kids = bool(re.search(
            r"\b(enfant|enfants|kid|kids|bambini|bambino|junior|bb|bébé|bebe|garçon|fille|baby)\b",
            text,
        ))
        if is_kids:
            trend_score -= 20

        is_hard = any(h in text for h in self._hard_to_sell)
        boring_patterns = [r"\bt shirt\b", r"\btee\b", r"\bchemise basique\b", r"\bbasic\b"]
        if any(re.search(p, text) for p in boring_patterns) and not style_tags:
            is_hard = True
            trend_score -= 15

        colors = self._extract_colors(title, dominant_color)
        color_appeal = self._color_appeal(colors)

        photo_score = 40.0
        if photo_count >= 4:
            photo_score += 25
        elif photo_count >= 2:
            photo_score += 15
        elif photo_count >= 1:
            photo_score += 5
        if photo_resolution >= 600:
            photo_score += 20
        elif photo_resolution >= 400:
            photo_score += 10
        photo_score = min(100, photo_score)

        overall = trend_score * 0.45 + color_appeal * 0.30 + photo_score * 0.25
        if is_hard:
            overall *= 0.6
        if is_kids:
            overall *= 0.7

        return AestheticAssessment(
            score=round(min(100, max(0, overall)), 1),
            trend_match=trend_match,
            color_appeal=round(color_appeal, 1),
            style_tags=style_tags,
            is_dated=is_dated,
            is_hard_to_sell=is_hard,
            is_kids_item=is_kids,
            photo_attractiveness=round(photo_score, 1),
        )
