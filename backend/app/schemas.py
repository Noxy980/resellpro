"""Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class OpportunityOut(BaseModel):
    id: int
    vinted_id: int
    title: str
    brand: str
    model: str
    category: str
    size: str
    condition: str
    price: float
    estimated_resale: float
    potential_profit: float
    profit_percent: float
    score: int
    demand_level: str
    selling_speed: str
    quick_sale_probability: float
    why_buy: str
    risk: str
    url: str
    image_url: str | None
    status: str
    found_at: datetime

    class Config:
        from_attributes = True


class OpportunityAction(BaseModel):
    action: str  # favorite, purchased, rejected


class InventoryCreate(BaseModel):
    title: str
    brand: str = ""
    model: str = ""
    size: str = ""
    condition: str = ""
    purchase_price: float
    planned_resale_price: float = 0
    notes: str = ""


class InventoryUpdate(BaseModel):
    title: str | None = None
    brand: str | None = None
    model: str | None = None
    size: str | None = None
    condition: str | None = None
    purchase_price: float | None = None
    planned_resale_price: float | None = None
    actual_sale_price: float | None = None
    status: str | None = None
    notes: str | None = None
    vinted_listing_url: str | None = None


class InventoryOut(BaseModel):
    id: int
    title: str
    brand: str
    model: str
    size: str
    condition: str
    purchase_price: float
    purchase_date: datetime
    planned_resale_price: float
    actual_sale_price: float | None
    sale_date: datetime | None
    status: str
    notes: str
    vinted_listing_url: str
    real_profit: float | None = None
    margin_percent: float | None = None

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str
    opportunity_id: int | None = None


class ChatResponse(BaseModel):
    reply: str
    ai_available: bool


class ListingGenerateRequest(BaseModel):
    brand: str
    condition: str
    size: str
    category: str
    extra_info: str = ""
    target_price: float = 0


class ListingOptimizeRequest(BaseModel):
    title: str
    description: str
    brand: str


class VintedConnectRequest(BaseModel):
    country: str = "fr"


class SettingsUpdate(BaseModel):
    openai_api_key: str | None = None
    monitor_enabled: bool | None = None
    poll_interval: int | None = None


class StatsOut(BaseModel):
    total_profit: float
    total_items_sold: int
    avg_profit: float
    avg_margin: float
    success_rate: float
    best_brands: list[dict[str, Any]]
    best_categories: list[dict[str, Any]]
    profit_timeline: list[dict[str, Any]]
