"""Discord webhook notifications — expert reseller format."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from curl_cffi import requests

if TYPE_CHECKING:
    from .analyzer import ListingAnalysis

logger = logging.getLogger(__name__)


class DiscordNotifier:
    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    def send_opportunity(self, analysis: ListingAnalysis) -> bool:
        if not self.webhook_url:
            logger.error("Discord webhook URL is not configured")
            return False

        demand_emoji = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(analysis.demand_level, "⚪")

        embed: dict = {
            "title": "🔥 Opportunity found",
            "color": 0x2ECC71 if analysis.opportunity_score >= 80 else 0xFF6B35,
            "fields": [
                {"name": "Item", "value": analysis.title[:256], "inline": False},
                {"name": "Brand", "value": analysis.brand or "N/A", "inline": True},
                {"name": "Model", "value": analysis.model[:128] or "N/A", "inline": True},
                {"name": "Price", "value": f"€{analysis.price:.2f}", "inline": True},
                {"name": "Estimated value", "value": f"€{analysis.estimated_resale_value:.2f}", "inline": True},
                {"name": "Potential profit", "value": f"€{analysis.potential_profit:.2f} ({analysis.profit_percent}%)", "inline": True},
                {"name": "Total score", "value": f"**{analysis.opportunity_score}/100**", "inline": True},
                {"name": "Demand", "value": f"{demand_emoji} {analysis.demand_level.title()} ({analysis.quick_sale_probability:.0f}% quick sale)", "inline": True},
                {"name": "Selling speed", "value": f"~{analysis.selling_speed}", "inline": True},
                {"name": "Why buy", "value": analysis.why_buy[:1024], "inline": False},
                {"name": "Risk", "value": analysis.risk[:1024], "inline": False},
                {"name": "Link", "value": f"[Open on Vinted]({analysis.url})", "inline": False},
            ],
            "footer": {
                "text": (
                    f"Size: {analysis.size} | Condition: {analysis.condition} | "
                    f"Ease: {analysis.ease_of_resale:.0f}/100"
                ),
            },
        }

        if analysis.image_url:
            embed["image"] = {"url": analysis.image_url}

        payload = {"embeds": [embed]}

        try:
            resp = requests.post(
                self.webhook_url, json=payload, timeout=15, impersonate="chrome131",
            )
            if resp.status_code in (200, 204):
                logger.info("Discord alert sent — %s (score %d)", analysis.title, analysis.opportunity_score)
                return True
            logger.error("Discord webhook failed (%d): %s", resp.status_code, resp.text[:300])
            return False
        except Exception as exc:
            logger.error("Discord notification error: %s", exc)
            return False
