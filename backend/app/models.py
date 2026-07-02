"""Modèle de données OnlyChat CRM.

Hiérarchie : User -> Membership(role) -> Agency -> TelegramAccount -> Conversation -> Message
Le vault et les tags sont au niveau du compte Telegram (persona).
Les ventes sont trackées via liens Dropfan (pas de PSP intégré).
"""
from datetime import datetime

from sqlalchemy import (Boolean, DateTime, Float, ForeignKey, Integer, String,
                        Text, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.utcnow()


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    memberships: Mapped[list["Membership"]] = relationship(back_populates="user")


class Agency(Base):
    __tablename__ = "agencies"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Paris")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    memberships: Mapped[list["Membership"]] = relationship(back_populates="agency")
    accounts: Mapped[list["TelegramAccount"]] = relationship(back_populates="agency")


class Membership(Base):
    """Rôles : owner / admin / manager / chatter."""
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("user_id", "agency_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    agency_id: Mapped[int] = mapped_column(ForeignKey("agencies.id"), index=True)
    role: Mapped[str] = mapped_column(String(20), default="chatter")

    user: Mapped["User"] = relationship(back_populates="memberships")
    agency: Mapped["Agency"] = relationship(back_populates="memberships")


class TelegramAccount(Base):
    """Un compte Telegram connecté (une persona). session_string = session Telethon."""
    __tablename__ = "telegram_accounts"
    id: Mapped[int] = mapped_column(primary_key=True)
    agency_id: Mapped[int] = mapped_column(ForeignKey("agencies.id"), index=True)
    label: Mapped[str] = mapped_column(String(120))            # ex. "Ashley"
    tg_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    session_string: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="disconnected")  # disconnected|connecting|connected|banned
    account_notes: Mapped[str] = mapped_column(Text, default="")             # consignes/scripts persona
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    agency: Mapped["Agency"] = relationship(back_populates="accounts")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="account")


class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("telegram_accounts.id"), index=True)
    name: Mapped[str] = mapped_column(String(50))              # SPENDER, WHALE, TW…
    color: Mapped[str] = mapped_column(String(20), default="#6366f1")


class Contact(Base):
    """Un fan (peer Telegram) rattaché à un compte persona."""
    __tablename__ = "contacts"
    __table_args__ = (UniqueConstraint("account_id", "tg_peer_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("telegram_accounts.id"), index=True)
    tg_peer_id: Mapped[int] = mapped_column(Integer, index=True)
    display_name: Mapped[str] = mapped_column(String(120))
    username: Mapped[str | None] = mapped_column(String(120), nullable=True)
    country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    bio: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    # Financial insights (qualification manuelle par le chatter)
    total_spent: Mapped[float] = mapped_column(Float, default=0.0)
    payday: Mapped[str | None] = mapped_column(String(64), nullable=True)
    salary: Mapped[str | None] = mapped_column(String(64), nullable=True)
    occupation: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tag_ids: Mapped[str] = mapped_column(String(255), default="")  # CSV d'ids de tags (simple pour MVP)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (UniqueConstraint("account_id", "contact_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("telegram_accounts.id"), index=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id"), index=True)
    last_message_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    last_message_preview: Mapped[str] = mapped_column(String(255), default="")
    unread_count: Mapped[int] = mapped_column(Integer, default=0)
    needs_reply: Mapped[bool] = mapped_column(Boolean, default=False)
    pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)

    account: Mapped["TelegramAccount"] = relationship(back_populates="conversations")
    contact: Mapped["Contact"] = relationship()
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)
    tg_message_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    direction: Mapped[str] = mapped_column(String(8))          # in | out
    body: Mapped[str] = mapped_column(Text, default="")
    media_id: Mapped[int | None] = mapped_column(ForeignKey("media.id"), nullable=True)
    # Attribution : quel membre a envoyé ce message (None = envoyé depuis le tel perso / inconnu)
    sent_by_membership_id: Mapped[int | None] = mapped_column(ForeignKey("memberships.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


class Media(Base):
    """Vault : un média réutilisable, optionnellement lié à une offre Dropfan."""
    __tablename__ = "media"
    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("telegram_accounts.id"), index=True)
    folder: Mapped[str] = mapped_column(String(120), default="All media")
    kind: Mapped[str] = mapped_column(String(20), default="photo")  # photo|video|audio|document
    filename: Mapped[str] = mapped_column(String(255))
    filepath: Mapped[str] = mapped_column(String(500))
    notes: Mapped[str] = mapped_column(Text, default="")
    # Monétisation Dropfan : si price > 0, l'envoi poste le lien Dropfan (pas le fichier)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    dropfan_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class MediaSend(Base):
    """Trace de chaque envoi de média (anti-doublon + attribution + statut de vente)."""
    __tablename__ = "media_sends"
    id: Mapped[int] = mapped_column(primary_key=True)
    media_id: Mapped[int] = mapped_column(ForeignKey("media.id"), index=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)
    sent_by_membership_id: Mapped[int | None] = mapped_column(ForeignKey("memberships.id"), nullable=True)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    paid: Mapped[bool] = mapped_column(Boolean, default=False)   # marqué payé (manuel MVP, webhook Dropfan plus tard)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Sale(Base):
    """Vente confirmée (saisie manuelle MVP ou futur webhook Dropfan)."""
    __tablename__ = "sales"
    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("telegram_accounts.id"), index=True)
    conversation_id: Mapped[int | None] = mapped_column(ForeignKey("conversations.id"), nullable=True)
    membership_id: Mapped[int | None] = mapped_column(ForeignKey("memberships.id"), nullable=True)
    kind: Mapped[str] = mapped_column(String(20), default="ppv")  # ppv|subscription|tip
    amount: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(20), default="dropfan")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
