"""Learning system — adapts to user preferences over time."""

from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import LearningPreference, UserAction


class LearningService:
    BRAND_PREFIX = "brand:"
    CATEGORY_PREFIX = "category:"
    REJECT_PENALTY = -3.0
    PURCHASE_BOOST = 5.0
    FAVORITE_BOOST = 2.0
    SOLD_BOOST = 8.0

    def record_action(
        self,
        db: Session,
        *,
        action_type: str,
        brand: str = "",
        category: str = "",
        model: str = "",
        score: int = 0,
    ) -> None:
        db.add(UserAction(
            action_type=action_type,
            brand=brand,
            category=category,
            model=model,
            score=score,
        ))

        delta = 0.0
        if action_type == "reject":
            delta = self.REJECT_PENALTY
        elif action_type == "purchase":
            delta = self.PURCHASE_BOOST
        elif action_type == "favorite":
            delta = self.FAVORITE_BOOST
        elif action_type == "sold":
            delta = self.SOLD_BOOST

        if brand:
            self._adjust(db, f"{self.BRAND_PREFIX}{brand.lower()}", delta)
        if category:
            self._adjust(db, f"{self.CATEGORY_PREFIX}{category.lower()}", delta)

        db.commit()

    def _adjust(self, db: Session, key: str, delta: float) -> None:
        pref = db.query(LearningPreference).filter(LearningPreference.key == key).first()
        if not pref:
            pref = LearningPreference(key=key, value=0, samples=0)
            db.add(pref)
        pref.samples += 1
        pref.value = max(-50, min(50, pref.value + delta))

    def get_brand_boost(self, db: Session, brand: str) -> float:
        pref = db.query(LearningPreference).filter(
            LearningPreference.key == f"{self.BRAND_PREFIX}{brand.lower()}"
        ).first()
        return pref.value if pref else 0.0

    def get_category_boost(self, db: Session, category: str) -> float:
        pref = db.query(LearningPreference).filter(
            LearningPreference.key == f"{self.CATEGORY_PREFIX}{category.lower()}"
        ).first()
        return pref.value if pref else 0.0

    def get_profile(self, db: Session) -> dict:
        prefs = db.query(LearningPreference).order_by(LearningPreference.value.desc()).all()
        actions = db.query(UserAction).count()
        top_brands = [p for p in prefs if p.key.startswith(self.BRAND_PREFIX)][:5]
        avoided_brands = [p for p in prefs if p.key.startswith(self.BRAND_PREFIX) and p.value < -5][:5]
        return {
            "total_actions": actions,
            "preferred_brands": [
                {"name": p.key.replace(self.BRAND_PREFIX, ""), "score": p.value, "samples": p.samples}
                for p in top_brands
            ],
            "avoided_brands": [
                {"name": p.key.replace(self.BRAND_PREFIX, ""), "score": p.value, "samples": p.samples}
                for p in avoided_brands
            ],
        }
