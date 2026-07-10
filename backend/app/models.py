"""Database models."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class OpportunityRecord(Base):
    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vinted_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(512))
    brand: Mapped[str] = mapped_column(String(128), default="")
    model: Mapped[str] = mapped_column(String(256), default="")
    category: Mapped[str] = mapped_column(String(64), default="")
    size: Mapped[str] = mapped_column(String(32), default="")
    condition: Mapped[str] = mapped_column(String(64), default="")
    price: Mapped[float] = mapped_column(Float)
    estimated_resale: Mapped[float] = mapped_column(Float)
    potential_profit: Mapped[float] = mapped_column(Float)
    profit_percent: Mapped[float] = mapped_column(Float, default=0)
    score: Mapped[int] = mapped_column(Integer)
    demand_level: Mapped[str] = mapped_column(String(16), default="medium")
    selling_speed: Mapped[str] = mapped_column(String(32), default="")
    quick_sale_probability: Mapped[float] = mapped_column(Float, default=0)
    why_buy: Mapped[str] = mapped_column(Text, default="")
    risk: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str] = mapped_column(String(512), default="")
    image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active")  # active, favorite, purchased, rejected
    raw_json: Mapped[str] = mapped_column(Text, default="{}")
    found_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class InventoryItem(Base):
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(512))
    brand: Mapped[str] = mapped_column(String(128), default="")
    model: Mapped[str] = mapped_column(String(256), default="")
    size: Mapped[str] = mapped_column(String(32), default="")
    condition: Mapped[str] = mapped_column(String(64), default="")
    purchase_price: Mapped[float] = mapped_column(Float)
    purchase_date: Mapped[datetime] = mapped_column(DateTime, default=_now)
    planned_resale_price: Mapped[float] = mapped_column(Float, default=0)
    actual_sale_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    sale_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="achete")
    photo_paths: Mapped[str] = mapped_column(Text, default="[]")
    notes: Mapped[str] = mapped_column(Text, default="")
    vinted_listing_url: Mapped[str] = mapped_column(String(512), default="")


class UserAction(Base):
    __tablename__ = "user_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action_type: Mapped[str] = mapped_column(String(32))  # reject, purchase, favorite
    brand: Mapped[str] = mapped_column(String(128), default="")
    category: Mapped[str] = mapped_column(String(64), default="")
    model: Mapped[str] = mapped_column(String(256), default="")
    score: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class LearningPreference(Base):
    __tablename__ = "learning_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(128), unique=True)
    value: Mapped[float] = mapped_column(Float, default=0)
    samples: Mapped[int] = mapped_column(Integer, default=0)


class VintedSession(Base):
    __tablename__ = "vinted_session"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    country: Mapped[str] = mapped_column(String(16), default="fr")
    is_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    username: Mapped[str] = mapped_column(String(128), default="")
    cookies_encrypted: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class DraftListing(Base):
    __tablename__ = "draft_listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(512), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    brand: Mapped[str] = mapped_column(String(128), default="")
    category: Mapped[str] = mapped_column(String(64), default="")
    size: Mapped[str] = mapped_column(String(32), default="")
    condition: Mapped[str] = mapped_column(String(64), default="")
    price: Mapped[float] = mapped_column(Float, default=0)
    keywords: Mapped[str] = mapped_column(Text, default="")
    photo_paths: Mapped[str] = mapped_column(Text, default="[]")
    status: Mapped[str] = mapped_column(String(32), default="draft")  # draft, ready, published
    ai_tips: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class AppSettings(Base):
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    openai_api_key_encrypted: Mapped[str] = mapped_column(Text, default="")  # stores OpenRouter key
    monitor_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    poll_interval: Mapped[int] = mapped_column(Integer, default=90)
    ai_recommendation: Mapped[str] = mapped_column(Text, default="")
