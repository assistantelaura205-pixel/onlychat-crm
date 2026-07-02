from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import current_user, require_membership
from ..database import get_db
from ..models import Media, TelegramAccount, User
from ..schemas import MediaIn, MediaOut

router = APIRouter(prefix="/api/agencies/{agency_id}/accounts/{account_id}/vault", tags=["vault"])


def _check(agency_id, account_id, user, db):
    require_membership(agency_id, user, db)
    acc = db.get(TelegramAccount, account_id)
    if acc is None or acc.agency_id != agency_id:
        raise HTTPException(404, "Compte introuvable")


@router.get("", response_model=list[MediaOut])
def list_media(agency_id: int, account_id: int, folder: str | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    _check(agency_id, account_id, user, db)
    q = db.query(Media).filter(Media.account_id == account_id)
    if folder and folder != "All media":
        q = q.filter(Media.folder == folder)
    return q.order_by(Media.created_at.desc()).all()


@router.post("", response_model=MediaOut)
def create_media(agency_id: int, account_id: int, body: MediaIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    _check(agency_id, account_id, user, db)
    m = Media(
        account_id=account_id, folder=body.folder, kind=body.kind, filename=body.filename,
        filepath=body.filepath, notes=body.notes, price=body.price, dropfan_url=body.dropfan_url,
    )
    db.add(m)
    db.commit()
    return m


@router.get("/folders")
def list_folders(agency_id: int, account_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    _check(agency_id, account_id, user, db)
    rows = db.query(Media.folder).filter(Media.account_id == account_id).distinct().all()
    return ["All media"] + sorted({r[0] for r in rows if r[0] and r[0] != "All media"})
