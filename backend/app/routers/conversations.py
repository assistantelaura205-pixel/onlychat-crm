from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..auth import current_user, require_membership
from ..database import get_db
from ..models import (Contact, Conversation, Media, MediaSend, Message,
                      Membership, TelegramAccount, User)
from ..schemas import (ContactOut, ContactUpdateIn, ConversationOut,
                       MessageOut, SendMessageIn)
from ..telegram_manager import manager
from ..ws import hub

router = APIRouter(prefix="/api/agencies/{agency_id}/accounts/{account_id}", tags=["conversations"])


def _csv_to_ids(s: str) -> list[int]:
    return [int(x) for x in s.split(",") if x.strip().isdigit()]


def _contact_out(c: Contact) -> ContactOut:
    return ContactOut(
        id=c.id, display_name=c.display_name, username=c.username, country=c.country,
        is_premium=c.is_premium, bio=c.bio, notes=c.notes, total_spent=c.total_spent,
        payday=c.payday, salary=c.salary, occupation=c.occupation, tag_ids=_csv_to_ids(c.tag_ids),
    )


def _check(agency_id, account_id, user, db) -> TelegramAccount:
    require_membership(agency_id, user, db)
    acc = db.get(TelegramAccount, account_id)
    if acc is None or acc.agency_id != agency_id:
        raise HTTPException(404, "Compte introuvable")
    return acc


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(
    agency_id: int, account_id: int,
    filter: str = Query("all"),      # all|new|unread|to_reply|paid
    q: str | None = None,
    user: User = Depends(current_user), db: Session = Depends(get_db),
):
    _check(agency_id, account_id, user, db)
    query = db.query(Conversation).filter(Conversation.account_id == account_id, Conversation.archived == False)  # noqa
    if filter == "unread":
        query = query.filter(Conversation.unread_count > 0)
    elif filter == "to_reply":
        query = query.filter(Conversation.needs_reply == True)  # noqa
    convs = query.order_by(desc(Conversation.pinned), desc(Conversation.last_message_at)).all()
    out = []
    for cv in convs:
        c = db.get(Contact, cv.contact_id)
        if q and q.lower() not in (c.display_name or "").lower():
            continue
        out.append(ConversationOut(
            id=cv.id, contact=_contact_out(c), last_message_at=cv.last_message_at,
            last_message_preview=cv.last_message_preview, unread_count=cv.unread_count,
            needs_reply=cv.needs_reply, pinned=cv.pinned, archived=cv.archived,
        ))
    return out


@router.get("/conversations/{conv_id}/messages", response_model=list[MessageOut])
def list_messages(agency_id: int, account_id: int, conv_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    _check(agency_id, account_id, user, db)
    cv = db.get(Conversation, conv_id)
    if cv is None or cv.account_id != account_id:
        raise HTTPException(404, "Conversation introuvable")
    cv.unread_count = 0
    db.commit()
    return db.query(Message).filter(Message.conversation_id == conv_id).order_by(Message.created_at).all()


@router.post("/conversations/{conv_id}/messages", response_model=MessageOut)
async def send_message(agency_id: int, account_id: int, conv_id: int, body: SendMessageIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    _check(agency_id, account_id, user, db)
    cv = db.get(Conversation, conv_id)
    if cv is None or cv.account_id != account_id:
        raise HTTPException(404, "Conversation introuvable")
    membership = db.query(Membership).filter(Membership.agency_id == agency_id, Membership.user_id == user.id).first()

    text = body.body
    media = None
    if body.media_id:
        media = db.get(Media, body.media_id)
        if media and media.price > 0 and media.dropfan_url:
            # PPV via Dropfan : on poste le teaser + le lien payant (pas le fichier)
            text = (text + "\n\n" if text else "") + f"🔒 Contenu exclusif ({media.price:.0f}€) 👉 {media.dropfan_url}"

    # Envoi Telegram réel si connecté, sinon mode démo (persistance seule)
    tg_msg_id = await manager.send_message(account_id, db.get(Contact, cv.contact_id).tg_peer_id, text) if text else None

    msg = Message(
        conversation_id=conv_id, tg_message_id=tg_msg_id, direction="out", body=text,
        media_id=body.media_id, sent_by_membership_id=membership.id if membership else None,
        created_at=datetime.utcnow(),
    )
    db.add(msg)
    if body.media_id:
        db.add(MediaSend(
            media_id=body.media_id, conversation_id=conv_id,
            sent_by_membership_id=membership.id if membership else None,
            price=media.price if media else 0.0,
        ))
    cv.last_message_at = msg.created_at
    cv.last_message_preview = (text or "[média]")[:120]
    cv.needs_reply = False
    db.commit()

    await hub.broadcast(agency_id, "message.new", {"conversation_id": conv_id, "direction": "out", "body": text})
    return msg


@router.put("/contacts/{contact_id}", response_model=ContactOut)
def update_contact(agency_id: int, account_id: int, contact_id: int, body: ContactUpdateIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    _check(agency_id, account_id, user, db)
    c = db.get(Contact, contact_id)
    if c is None or c.account_id != account_id:
        raise HTTPException(404, "Contact introuvable")
    if body.notes is not None:
        c.notes = body.notes
    if body.total_spent is not None:
        c.total_spent = body.total_spent
    if body.payday is not None:
        c.payday = body.payday
    if body.salary is not None:
        c.salary = body.salary
    if body.occupation is not None:
        c.occupation = body.occupation
    if body.tag_ids is not None:
        c.tag_ids = ",".join(str(i) for i in body.tag_ids)
    db.commit()
    return _contact_out(c)


@router.post("/conversations/{conv_id}/pin")
def toggle_pin(agency_id: int, account_id: int, conv_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    _check(agency_id, account_id, user, db)
    cv = db.get(Conversation, conv_id)
    if cv is None:
        raise HTTPException(404)
    cv.pinned = not cv.pinned
    db.commit()
    return {"pinned": cv.pinned}
