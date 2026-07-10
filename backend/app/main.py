"""FastAPI application — ResellPro desktop backend."""

from __future__ import annotations

import json
import logging
import os
import webbrowser
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .database import get_db, init_db
from .models import AppSettings, ChatMessage, DraftListing, InventoryItem, OpportunityRecord, VintedSession
from .schemas import (
    ChatRequest,
    ChatResponse,
    ChatMessageOut,
    InventoryCreate,
    InventoryOut,
    InventoryUpdate,
    ListingGenerateRequest,
    ListingOptimizeRequest,
    OpportunityAction,
    OpportunityOut,
    SettingsUpdate,
    StatsOut,
    VintedConnectRequest,
)
from .security import decrypt, encrypt
from .services.openrouter_ai import OpenRouterAI
from .services.learning_service import LearningService
from .services.monitor_service import monitor
from .services.photo_service import OUTPUT_DIR, enhance_photo
from .services.vinted_account import VintedAccountService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("resellpro")

learning = LearningService()
_ai_service: OpenRouterAI | None = None

DEFAULT_OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
_cors_origins = os.environ.get("ALLOWED_ORIGINS", "*").strip()
CORS_ORIGINS = (
    ["*"]
    if _cors_origins in ("", "*")
    else [o.strip() for o in _cors_origins.split(",") if o.strip()]
)


def _get_ai(db: Session) -> OpenRouterAI:
    global _ai_service
    settings = db.query(AppSettings).first()
    key = DEFAULT_OPENROUTER_KEY
    if settings and settings.openai_api_key_encrypted:
        key = decrypt(settings.openai_api_key_encrypted) or key
    _ai_service = OpenRouterAI(key)
    return _ai_service


def _opp_to_out(record: OpportunityRecord) -> OpportunityOut:
    return OpportunityOut(
        id=record.id,
        vinted_id=record.vinted_id,
        title=record.title,
        brand=record.brand,
        model=record.model,
        category=record.category,
        size=record.size,
        condition=record.condition,
        price=record.price,
        estimated_resale=record.estimated_resale,
        potential_profit=record.potential_profit,
        profit_percent=record.profit_percent,
        score=record.score,
        demand_level=record.demand_level,
        selling_speed=record.selling_speed,
        quick_sale_probability=record.quick_sale_probability,
        why_buy=record.why_buy,
        risk=record.risk,
        url=record.url,
        image_url=record.image_url,
        status=record.status,
        found_at=record.found_at,
    )


def _save_opportunity(db: Session, data: dict) -> OpportunityRecord:
    existing = db.query(OpportunityRecord).filter(
        OpportunityRecord.vinted_id == data["vinted_id"]
    ).first()
    if existing:
        return existing

    record = OpportunityRecord(
        vinted_id=data["vinted_id"],
        title=data["title"],
        brand=data.get("brand", ""),
        model=data.get("model", ""),
        category=data.get("category", ""),
        size=data.get("size", ""),
        condition=data.get("condition", ""),
        price=data["price"],
        estimated_resale=data["estimated_resale"],
        potential_profit=data["potential_profit"],
        profit_percent=data.get("profit_percent", 0),
        score=data["score"],
        demand_level=data.get("demand_level", "medium"),
        selling_speed=data.get("selling_speed", ""),
        quick_sale_probability=data.get("quick_sale_probability", 0),
        why_buy=data.get("why_buy", ""),
        risk=data.get("risk", ""),
        url=data.get("url", ""),
        image_url=data.get("image_url"),
        raw_json=json.dumps(data),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Auto-configure OpenRouter API key on first launch
    from .database import SessionLocal
    db = SessionLocal()
    try:
        settings = db.query(AppSettings).first()
        if not settings:
            settings = AppSettings()
            db.add(settings)
        if DEFAULT_OPENROUTER_KEY and not settings.openai_api_key_encrypted:
            settings.openai_api_key_encrypted = encrypt(DEFAULT_OPENROUTER_KEY)
            db.commit()
            logger.info("OpenRouter API key configured automatically")
    finally:
        db.close()
    if os.environ.get("MONITOR_AUTO_START", "false").lower() == "true":
        monitor.start()
        logger.info("Background monitor started")
    else:
        logger.info("Background monitor disabled — scans manuels uniquement")
    yield
    monitor.stop()


app = FastAPI(title="ResellPro", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if "*" in CORS_ORIGINS else CORS_ORIGINS,
    allow_origin_regex=r"https://.*\.netlify\.app$",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    """Réponse rapide — utilisé pour réveiller Render (plan gratuit)."""
    return {"ok": True, "service": "resellpro", "status": monitor.status.get("status", "idle")}


# ── Auth / Vinted ──────────────────────────────────────────────────────────

@app.post("/api/vinted/connect")
def connect_vinted(req: VintedConnectRequest, db: Session = Depends(get_db)):
    try:
        monitor.client._ensure_session()
        session = db.query(VintedSession).first()
        if not session:
            session = VintedSession()
            db.add(session)
        session.country = req.country
        session.is_connected = True
        session.username = "Connected"
        session.updated_at = datetime.now(timezone.utc)
        db.commit()
        return {"connected": True, "country": req.country, "message": "Vinted session active"}
    except Exception as exc:
        raise HTTPException(500, f"Connection failed: {exc}")


@app.get("/api/vinted/status")
def vinted_status(db: Session = Depends(get_db)):
    session = db.query(VintedSession).first()
    return {
        "connected": session.is_connected if session else False,
        "country": session.country if session else "fr",
        "username": session.username if session else "",
    }


# ── Opportunities ────────────────────────────────────────────────────────────

@app.get("/api/opportunities", response_model=list[OpportunityOut])
def list_opportunities(
    status: str = "active",
    search: str = "",
    min_score: int = 0,
    brand: str = "",
    max_price: float = 0,
    min_profit: float = 0,
    category: str = "",
    db: Session = Depends(get_db),
):
    q = db.query(OpportunityRecord).filter(OpportunityRecord.status == status)
    if min_score:
        q = q.filter(OpportunityRecord.score >= min_score)
    if search:
        q = q.filter(OpportunityRecord.title.ilike(f"%{search}%"))
    if brand:
        q = q.filter(OpportunityRecord.brand.ilike(f"%{brand}%"))
    if max_price > 0:
        q = q.filter(OpportunityRecord.price <= max_price)
    if min_profit > 0:
        q = q.filter(OpportunityRecord.potential_profit >= min_profit)
    if category:
        q = q.filter(OpportunityRecord.category.ilike(f"%{category}%"))
    records = q.order_by(OpportunityRecord.score.desc(), OpportunityRecord.found_at.desc()).limit(100).all()
    return [_opp_to_out(r) for r in records]


@app.get("/api/opportunities/{opp_id}", response_model=OpportunityOut)
def get_opportunity(opp_id: int, db: Session = Depends(get_db)):
    record = db.query(OpportunityRecord).filter(OpportunityRecord.id == opp_id).first()
    if not record:
        raise HTTPException(404, "Not found")
    return _opp_to_out(record)


@app.post("/api/opportunities/{opp_id}/action")
def opportunity_action(opp_id: int, action: OpportunityAction, db: Session = Depends(get_db)):
    record = db.query(OpportunityRecord).filter(OpportunityRecord.id == opp_id).first()
    if not record:
        raise HTTPException(404, "Not found")

    mapping = {"favorite": "favorite", "purchased": "purchased", "rejected": "rejected"}
    record.status = mapping.get(action.action, record.status)
    db.commit()

    learning.record_action(
        db,
        action_type=action.action,
        brand=record.brand,
        category=record.category,
        model=record.model,
        score=record.score,
    )

    if action.action == "purchased":
        inv = InventoryItem(
            title=record.title,
            brand=record.brand,
            model=record.model,
            size=record.size,
            condition=record.condition,
            purchase_price=record.price,
            planned_resale_price=record.estimated_resale,
            notes=f"From opportunity #{record.id}",
        )
        db.add(inv)

    db.commit()
    return {"ok": True, "status": record.status}


@app.post("/api/opportunities/scan")
def trigger_scan(reset_seen: bool = False, db: Session = Depends(get_db)):
    try:
        results, stats = monitor.scan_once(reset_seen=reset_seen)
    except Exception as exc:
        logger.exception("Scan failed")
        raise HTTPException(500, detail=str(exc)) from exc
    saved = []
    for data in results:
        record = _save_opportunity(db, data)
        saved.append(_opp_to_out(record))
    return {"found": len(saved), "opportunities": saved, "stats": stats}


@app.get("/api/vinted/diagnostic")
def vinted_diagnostic():
    return monitor.client.test_connection()


@app.get("/api/monitor/status")
def monitor_status():
    return monitor.status


# ── AI Assistant ───────────────────────────────────────────────────────────

@app.get("/api/ai/history", response_model=list[ChatMessageOut])
def get_chat_history(limit: int = 200, db: Session = Depends(get_db)):
    msgs = (
        db.query(ChatMessage)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
        .all()
    )
    return msgs


@app.delete("/api/ai/history")
def clear_chat_history(db: Session = Depends(get_db)):
    db.query(ChatMessage).delete()
    db.commit()
    return {"ok": True}


@app.post("/api/ai/chat", response_model=ChatResponse)
def ai_chat(req: ChatRequest, db: Session = Depends(get_db)):
    ai = _get_ai(db)
    context = None
    if req.opportunity_id:
        record = db.query(OpportunityRecord).filter(OpportunityRecord.id == req.opportunity_id).first()
        if record:
            context = {"opportunity": {
                "title": record.title, "brand": record.brand, "price": record.price,
                "estimated_resale": record.estimated_resale, "potential_profit": record.potential_profit,
                "score": record.score, "demand_level": record.demand_level,
                "selling_speed": record.selling_speed, "why_buy": record.why_buy, "risk": record.risk,
            }}

    db.add(ChatMessage(role="user", content=req.message))
    db.commit()

    reply = ai.chat(req.message, context)

    db.add(ChatMessage(role="assistant", content=reply))
    db.commit()

    return ChatResponse(reply=reply, ai_available=ai.available)


@app.post("/api/ai/generate-listing")
def generate_listing(req: ListingGenerateRequest, db: Session = Depends(get_db)):
    ai = _get_ai(db)
    return ai.generate_listing(
        brand=req.brand, condition=req.condition, size=req.size,
        category=req.category, extra_info=req.extra_info, target_price=req.target_price,
    )


@app.post("/api/ai/optimize-listing")
def optimize_listing(req: ListingOptimizeRequest, db: Session = Depends(get_db)):
    ai = _get_ai(db)
    return ai.optimize_listing(req.title, req.description, req.brand)


@app.post("/api/ai/analyze/{opp_id}")
def analyze_opportunity(opp_id: int, db: Session = Depends(get_db)):
    record = db.query(OpportunityRecord).filter(OpportunityRecord.id == opp_id).first()
    if not record:
        raise HTTPException(404, "Not found")
    ai = _get_ai(db)
    opp = {"title": record.title, "brand": record.brand, "price": record.price,
           "estimated_resale": record.estimated_resale, "potential_profit": record.potential_profit,
           "score": record.score, "demand_level": record.demand_level,
           "selling_speed": record.selling_speed, "why_buy": record.why_buy, "risk": record.risk}
    return {"analysis": ai.analyze_opportunity(opp)}


@app.post("/api/ai/trends")
def ai_trends(db: Session = Depends(get_db)):
    ai = _get_ai(db)
    return {"analysis": ai.trend_analysis()}


@app.post("/api/ai/price")
def ai_price(brand: str, model: str, condition: str, category: str, db: Session = Depends(get_db)):
    ai = _get_ai(db)
    return {"recommendation": ai.recommend_price(brand, model, condition, category)}


# ── Vinted Account ─────────────────────────────────────────────────────────

@app.get("/api/vinted/profile")
def vinted_profile(db: Session = Depends(get_db)):
    svc = VintedAccountService(monitor.client)
    profile = svc.get_profile()
    if profile.get("is_connected") and profile.get("login"):
        session = db.query(VintedSession).first()
        if session:
            session.username = profile["login"]
            db.commit()
    return profile


@app.get("/api/vinted/listings")
def vinted_listings(db: Session = Depends(get_db)):
    svc = VintedAccountService(monitor.client)
    profile = svc.get_profile()
    if not profile.get("id"):
        return {"listings": [], "message": "Connectez votre compte Vinted"}
    return {"listings": svc.get_my_listings(profile["id"])}


# ── Draft Listings ─────────────────────────────────────────────────────────

@app.get("/api/drafts")
def list_drafts(db: Session = Depends(get_db)):
    drafts = db.query(DraftListing).order_by(DraftListing.created_at.desc()).all()
    return [{"id": d.id, "title": d.title, "brand": d.brand, "price": d.price,
             "status": d.status, "created_at": d.created_at.isoformat()} for d in drafts]


@app.post("/api/drafts")
def create_draft(data: ListingGenerateRequest, db: Session = Depends(get_db)):
    ai = _get_ai(db)
    generated = ai.generate_listing(
        brand=data.brand, condition=data.condition, size=data.size,
        category=data.category, extra_info=data.extra_info, target_price=data.target_price,
    )
    draft = DraftListing(
        title=generated.get("title", ""),
        description=generated.get("description", ""),
        brand=data.brand, category=data.category, size=data.size,
        condition=data.condition,
        price=float(generated.get("recommended_price", data.target_price) or 0),
        keywords=generated.get("keywords", ""),
        ai_tips=generated.get("selling_tips", ""),
        status="ready",
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return {"id": draft.id, **generated, "publish_url": VintedAccountService(monitor.client).prepare_listing_url({})}


@app.get("/api/drafts/{draft_id}")
def get_draft(draft_id: int, db: Session = Depends(get_db)):
    d = db.query(DraftListing).filter(DraftListing.id == draft_id).first()
    if not d:
        raise HTTPException(404)
    return {"id": d.id, "title": d.title, "description": d.description, "brand": d.brand,
            "category": d.category, "size": d.size, "condition": d.condition,
            "price": d.price, "keywords": d.keywords, "ai_tips": d.ai_tips, "status": d.status}


# ── Photo Enhancement ──────────────────────────────────────────────────────

@app.post("/api/photos/enhance")
async def enhance_photo_endpoint(file: UploadFile = File(...), remove_bg: bool = False):
    content = await file.read()
    path, _ = enhance_photo(content, remove_bg=remove_bg)
    return {"path": path, "filename": Path(path).name}


@app.get("/api/photos/{filename}")
def get_enhanced_photo(filename: str):
    path = OUTPUT_DIR / filename
    if not path.exists():
        raise HTTPException(404)
    return FileResponse(path)


# ── Inventory ──────────────────────────────────────────────────────────────

@app.get("/api/inventory", response_model=list[InventoryOut])
def list_inventory(status: str | None = None, db: Session = Depends(get_db)):
    q = db.query(InventoryItem)
    if status:
        q = q.filter(InventoryItem.status == status)
    items = q.order_by(InventoryItem.purchase_date.desc()).all()
    result = []
    for item in items:
        profit = margin = None
        if item.actual_sale_price is not None:
            profit = item.actual_sale_price - item.purchase_price
            margin = (profit / item.purchase_price * 100) if item.purchase_price else 0
        result.append(InventoryOut(
            id=item.id, title=item.title, brand=item.brand, model=item.model,
            size=item.size, condition=item.condition, purchase_price=item.purchase_price,
            purchase_date=item.purchase_date, planned_resale_price=item.planned_resale_price,
            actual_sale_price=item.actual_sale_price, sale_date=item.sale_date,
            status=item.status, notes=item.notes, vinted_listing_url=item.vinted_listing_url,
            real_profit=profit, margin_percent=margin,
        ))
    return result


@app.post("/api/inventory", response_model=InventoryOut)
def create_inventory(item: InventoryCreate, db: Session = Depends(get_db)):
    inv = InventoryItem(**item.model_dump())
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return InventoryOut(
        id=inv.id, title=inv.title, brand=inv.brand, model=inv.model,
        size=inv.size, condition=inv.condition, purchase_price=inv.purchase_price,
        purchase_date=inv.purchase_date, planned_resale_price=inv.planned_resale_price,
        actual_sale_price=None, sale_date=None, status=inv.status,
        notes=inv.notes, vinted_listing_url=inv.vinted_listing_url,
    )


@app.patch("/api/inventory/{item_id}", response_model=InventoryOut)
def update_inventory(item_id: int, update: InventoryUpdate, db: Session = Depends(get_db)):
    inv = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not inv:
        raise HTTPException(404)
    for k, v in update.model_dump(exclude_none=True).items():
        setattr(inv, k, v)
    if update.status in ("sold", "vendu") and update.actual_sale_price:
        inv.sale_date = datetime.now(timezone.utc)
        learning.record_action(db, action_type="sold", brand=inv.brand, category="")
    db.commit()
    db.refresh(inv)
    profit = (inv.actual_sale_price - inv.purchase_price) if inv.actual_sale_price else None
    margin = (profit / inv.purchase_price * 100) if profit and inv.purchase_price else None
    return InventoryOut(
        id=inv.id, title=inv.title, brand=inv.brand, model=inv.model,
        size=inv.size, condition=inv.condition, purchase_price=inv.purchase_price,
        purchase_date=inv.purchase_date, planned_resale_price=inv.planned_resale_price,
        actual_sale_price=inv.actual_sale_price, sale_date=inv.sale_date,
        status=inv.status, notes=inv.notes, vinted_listing_url=inv.vinted_listing_url,
        real_profit=profit, margin_percent=margin,
    )


@app.delete("/api/inventory/{item_id}")
def delete_inventory(item_id: int, db: Session = Depends(get_db)):
    inv = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not inv:
        raise HTTPException(404)
    db.delete(inv)
    db.commit()
    return {"ok": True}


# ── Dashboard ──────────────────────────────────────────────────────────────

@app.get("/api/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from src.seasonal import get_current_season

    season = get_current_season()
    opps = db.query(OpportunityRecord).filter(
        OpportunityRecord.status == "active"
    ).order_by(OpportunityRecord.score.desc()).limit(5).all()
    inventory = db.query(InventoryItem).all()
    sold_statuses = {"sold", "vendu", "termine", "completed"}
    sold = [i for i in inventory if i.status in sold_statuses and i.actual_sale_price]
    total_profit = sum(i.actual_sale_price - i.purchase_price for i in sold)
    potential = sum(o.potential_profit for o in opps)

    tips = {
        "été": "Privilégiez les t-shirts Nike/Adidas, shorts Carhartt et sneakers légères — forte demande estivale.",
        "hiver": "Ciblez doudounes The North Face, pulls Stone Island et boots — les marges hivernales sont excellentes.",
        "printemps": "Vestes légères, sweats et polos Lacoste se vendent vite en transition de saison.",
        "automne": "Parkas, fleece Patagonia et cargos Carhartt — préparez le stock avant la montée des prix.",
    }

    return {
        "season": season.name,
        "season_keywords": season.keywords[:8],
        "top_opportunities": [_opp_to_out(o) for o in opps],
        "opportunity_count": db.query(OpportunityRecord).filter(OpportunityRecord.status == "active").count(),
        "potential_profit_today": round(potential, 2),
        "stock_count": len([i for i in inventory if i.status not in sold_statuses | {"envoye", "shipped"}]),
        "sold_count": len(sold),
        "total_profit": round(total_profit, 2),
        "ai_recommendation": tips.get(season.name, "Scannez les opportunités pour démarrer votre activité."),
        "monitor": monitor.status,
    }


@app.get("/api/dashboard/ai-tip")
def get_dashboard_ai_tip(db: Session = Depends(get_db)):
    """Optional slow endpoint — AI tip loaded separately so dashboard stays fast."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from src.seasonal import get_current_season

    season = get_current_season()
    ai = _get_ai(db)
    if not ai.available:
        return {"tip": "Configurez votre clé OpenRouter pour des conseils personnalisés."}
    try:
        tip = ai.chat(
            f"Donne UN conseil court (2 phrases max) pour un revendeur Vinted en {season.name}. "
            "Quoi acheter cette saison ?"
        )
        return {"tip": tip}
    except Exception:
        return {"tip": "Conseil IA indisponible pour le moment."}


# ── Statistics ─────────────────────────────────────────────────────────────

@app.get("/api/statistics", response_model=StatsOut)
def get_statistics(db: Session = Depends(get_db)):
    sold = db.query(InventoryItem).filter(
        InventoryItem.status.in_(["sold", "vendu", "termine"]),
        InventoryItem.actual_sale_price.isnot(None),
    ).all()

    total_profit = sum(i.actual_sale_price - i.purchase_price for i in sold)
    avg_profit = total_profit / len(sold) if sold else 0
    margins = [
        (i.actual_sale_price - i.purchase_price) / i.purchase_price * 100
        for i in sold if i.purchase_price > 0
    ]
    avg_margin = sum(margins) / len(margins) if margins else 0

    brand_profits: dict[str, float] = {}
    for i in sold:
        brand_profits[i.brand] = brand_profits.get(i.brand, 0) + (i.actual_sale_price - i.purchase_price)
    best_brands = sorted(
        [{"brand": b, "profit": p} for b, p in brand_profits.items()],
        key=lambda x: x["profit"], reverse=True,
    )[:5]

    all_inv = db.query(InventoryItem).count()
    success_rate = len(sold) / all_inv * 100 if all_inv else 0

    timeline = [
        {"date": i.sale_date.isoformat() if i.sale_date else "", "profit": i.actual_sale_price - i.purchase_price}
        for i in sold if i.sale_date
    ]

    return StatsOut(
        total_profit=round(total_profit, 2),
        total_items_sold=len(sold),
        avg_profit=round(avg_profit, 2),
        avg_margin=round(avg_margin, 1),
        success_rate=round(success_rate, 1),
        best_brands=best_brands,
        best_categories=[],
        profit_timeline=timeline,
    )


# ── Learning / Profile ─────────────────────────────────────────────────────

@app.get("/api/profile")
def get_profile(db: Session = Depends(get_db)):
    return learning.get_profile(db)


# ── Settings ───────────────────────────────────────────────────────────────

@app.get("/api/settings")
def get_settings(db: Session = Depends(get_db)):
    s = db.query(AppSettings).first()
    if not s:
        s = AppSettings()
        db.add(s)
        db.commit()
    return {
        "monitor_enabled": s.monitor_enabled,
        "poll_interval": s.poll_interval,
        "has_openai_key": bool(s.openai_api_key_encrypted or DEFAULT_OPENROUTER_KEY),
        "ai_provider": "OpenRouter (free models)",
    }


@app.patch("/api/settings")
def update_settings(update: SettingsUpdate, db: Session = Depends(get_db)):
    s = db.query(AppSettings).first()
    if not s:
        s = AppSettings()
        db.add(s)
    if update.openai_api_key is not None:
        s.openai_api_key_encrypted = encrypt(update.openai_api_key)
    if update.monitor_enabled is not None:
        s.monitor_enabled = update.monitor_enabled
    if update.poll_interval is not None:
        s.poll_interval = update.poll_interval
    db.commit()
    return {"ok": True}


# ── Callback for monitor ───────────────────────────────────────────────────

def _on_new_opportunity(data: dict):
    from .database import SessionLocal
    db = SessionLocal()
    try:
        _save_opportunity(db, data)
    finally:
        db.close()


monitor.set_callback(_on_new_opportunity)
