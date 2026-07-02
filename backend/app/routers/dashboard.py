from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth import current_user, require_membership
from ..database import get_db
from ..models import (Conversation, Membership, Sale, TelegramAccount, User)
from ..schemas import DashboardOut

router = APIRouter(prefix="/api/agencies/{agency_id}/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardOut)
def dashboard(agency_id: int, account_id: int | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_membership(agency_id, user, db)

    acc_ids = [a.id for a in db.query(TelegramAccount).filter(TelegramAccount.agency_id == agency_id).all()]
    if account_id:
        acc_ids = [account_id] if account_id in acc_ids else []

    sales = db.query(Sale).filter(Sale.account_id.in_(acc_ids)).all() if acc_ids else []
    total = sum(s.amount for s in sales)
    ppv = sum(s.amount for s in sales if s.kind == "ppv")
    sub = sum(s.amount for s in sales if s.kind == "subscription")
    tip = sum(s.amount for s in sales if s.kind == "tip")

    new_convs = db.query(func.count(Conversation.id)).filter(Conversation.account_id.in_(acc_ids)).scalar() if acc_ids else 0

    # Perf par membre (attribution des ventes)
    per_member = []
    for m in db.query(Membership).filter(Membership.agency_id == agency_id).all():
        u = db.get(User, m.user_id)
        rev = sum(s.amount for s in sales if s.membership_id == m.id)
        per_member.append({"name": u.name, "email": u.email, "role": m.role, "revenue": rev})

    return DashboardOut(
        total_earnings=total, ppv_earnings=ppv, subscription_earnings=sub, tip_earnings=tip,
        new_conversations=new_convs or 0, response_rate=100.0,
        conversion_rate=round((len([s for s in sales]) / new_convs * 100) if new_convs else 0.0, 1),
        per_member=per_member,
    )
