from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import current_user, hash_password, require_membership
from ..database import get_db
from ..models import Agency, Membership, User
from ..schemas import AgencyOut, InviteIn, MemberOut

router = APIRouter(prefix="/api/agencies", tags=["agencies"])


@router.get("", response_model=list[AgencyOut])
def list_agencies(user: User = Depends(current_user), db: Session = Depends(get_db)):
    out = []
    for m in db.query(Membership).filter(Membership.user_id == user.id).all():
        ag = db.get(Agency, m.agency_id)
        out.append(AgencyOut(id=ag.id, name=ag.name, timezone=ag.timezone, role=m.role))
    return out


@router.get("/{agency_id}/members", response_model=list[MemberOut])
def members(agency_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_membership(agency_id, user, db)
    out = []
    for m in db.query(Membership).filter(Membership.agency_id == agency_id).all():
        u = db.get(User, m.user_id)
        out.append(MemberOut(id=m.id, user_id=u.id, name=u.name, email=u.email, role=m.role))
    return out


@router.post("/{agency_id}/invite", response_model=MemberOut)
def invite(agency_id: int, body: InviteIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_membership(agency_id, user, db, roles=("owner", "admin"))
    if body.role not in ("admin", "manager", "chatter"):
        raise HTTPException(400, "Rôle invalide")
    invited = db.query(User).filter(User.email == body.email).first()
    if invited is None:
        invited = User(email=body.email, name=body.name, password_hash=hash_password(body.password))
        db.add(invited)
        db.flush()
    if db.query(Membership).filter(Membership.agency_id == agency_id, Membership.user_id == invited.id).first():
        raise HTTPException(400, "Déjà membre")
    m = Membership(user_id=invited.id, agency_id=agency_id, role=body.role)
    db.add(m)
    db.commit()
    return MemberOut(id=m.id, user_id=invited.id, name=invited.name, email=invited.email, role=m.role)
