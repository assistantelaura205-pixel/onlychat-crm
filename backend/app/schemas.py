"""Schémas Pydantic (I/O API)."""
from datetime import datetime

from pydantic import BaseModel, EmailStr


# --- Auth ---
class RegisterIn(BaseModel):
    email: EmailStr
    name: str
    password: str
    agency_name: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    name: str

    class Config:
        from_attributes = True


# --- Agence / membres ---
class AgencyOut(BaseModel):
    id: int
    name: str
    timezone: str
    role: str | None = None

    class Config:
        from_attributes = True


class MemberOut(BaseModel):
    id: int
    user_id: int
    name: str
    email: str
    role: str


class InviteIn(BaseModel):
    email: EmailStr
    name: str
    role: str = "chatter"
    password: str


# --- Comptes Telegram ---
class AccountOut(BaseModel):
    id: int
    label: str
    status: str
    tg_user_id: int | None = None
    account_notes: str = ""

    class Config:
        from_attributes = True


class AccountCreateIn(BaseModel):
    label: str


class AccountNotesIn(BaseModel):
    account_notes: str


# --- Tags ---
class TagOut(BaseModel):
    id: int
    name: str
    color: str

    class Config:
        from_attributes = True


class TagIn(BaseModel):
    name: str
    color: str = "#6366f1"


# --- Contacts / conversations / messages ---
class ContactOut(BaseModel):
    id: int
    display_name: str
    username: str | None
    country: str | None
    is_premium: bool
    bio: str
    notes: str
    total_spent: float
    payday: str | None
    salary: str | None
    occupation: str | None
    tag_ids: list[int]

    class Config:
        from_attributes = True


class ContactUpdateIn(BaseModel):
    notes: str | None = None
    total_spent: float | None = None
    payday: str | None = None
    salary: str | None = None
    occupation: str | None = None
    tag_ids: list[int] | None = None


class ConversationOut(BaseModel):
    id: int
    contact: ContactOut
    last_message_at: datetime
    last_message_preview: str
    unread_count: int
    needs_reply: bool
    pinned: bool
    archived: bool

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    id: int
    direction: str
    body: str
    media_id: int | None
    sent_by_membership_id: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class SendMessageIn(BaseModel):
    body: str = ""
    media_id: int | None = None


# --- Vault ---
class MediaOut(BaseModel):
    id: int
    folder: str
    kind: str
    filename: str
    notes: str
    price: float
    dropfan_url: str | None

    class Config:
        from_attributes = True


class MediaIn(BaseModel):
    folder: str = "All media"
    kind: str = "photo"
    filename: str
    filepath: str = ""
    notes: str = ""
    price: float = 0.0
    dropfan_url: str | None = None


# --- Ventes ---
class SaleIn(BaseModel):
    conversation_id: int | None = None
    kind: str = "ppv"
    amount: float
    source: str = "dropfan"


class DashboardOut(BaseModel):
    total_earnings: float
    ppv_earnings: float
    subscription_earnings: float
    tip_earnings: float
    new_conversations: int
    response_rate: float
    conversion_rate: float
    per_member: list[dict]
