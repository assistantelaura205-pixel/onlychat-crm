from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import current_user, require_membership
from ..database import get_db
from ..models import TelegramAccount, Tag, User
from ..schemas import (AccountCreateIn, AccountNotesIn, AccountOut, TagIn,
                       TagOut)
from ..telegram_manager import manager

router = APIRouter(prefix="/api/agencies/{agency_id}/accounts", tags=["accounts"])


def _get_account(agency_id: int, account_id: int, db: Session) -> TelegramAccount:
    acc = db.get(TelegramAccount, account_id)
    if acc is None or acc.agency_id != agency_id:
        raise HTTPException(404, "Compte introuvable")
    return acc


@router.get("", response_model=list[AccountOut])
def list_accounts(agency_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_membership(agency_id, user, db)
    return db.query(TelegramAccount).filter(TelegramAccount.agency_id == agency_id).all()


@router.post("", response_model=AccountOut)
def create_account(agency_id: int, body: AccountCreateIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_membership(agency_id, user, db, roles=("owner", "admin"))
    acc = TelegramAccount(agency_id=agency_id, label=body.label, status="disconnected")
    db.add(acc)
    db.commit()
    return acc


@router.put("/{account_id}/notes", response_model=AccountOut)
def update_notes(agency_id: int, account_id: int, body: AccountNotesIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_membership(agency_id, user, db)
    acc = _get_account(agency_id, account_id, db)
    acc.account_notes = body.account_notes
    db.commit()
    return acc


# --- Connexion Telegram (QR) ---
@router.post("/{account_id}/qr/start")
async def qr_start(agency_id: int, account_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_membership(agency_id, user, db, roles=("owner", "admin", "manager"))
    acc = _get_account(agency_id, account_id, db)
    acc.status = "connecting"
    db.commit()
    return await manager.start_qr_login(account_id)


@router.get("/{account_id}/qr/poll")
async def qr_poll(agency_id: int, account_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_membership(agency_id, user, db)
    acc = _get_account(agency_id, account_id, db)
    result = await manager.poll_qr_login(account_id)
    if result.get("status") == "connected":
        acc.status = "connected"
        acc.session_string = result["session_string"]
        acc.tg_user_id = result.get("tg_user_id")
        db.commit()
        return {"status": "connected"}
    return result


# --- Tags ---
@router.get("/{account_id}/tags", response_model=list[TagOut])
def list_tags(agency_id: int, account_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_membership(agency_id, user, db)
    _get_account(agency_id, account_id, db)
    return db.query(Tag).filter(Tag.account_id == account_id).all()


@router.post("/{account_id}/tags", response_model=TagOut)
def create_tag(agency_id: int, account_id: int, body: TagIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_membership(agency_id, user, db)
    _get_account(agency_id, account_id, db)
    tag = Tag(account_id=account_id, name=body.name, color=body.color)
    db.add(tag)
    db.commit()
    return tag
