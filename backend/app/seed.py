"""Données de démo pour développer/démontrer l'UI sans vrai Telegram.

Login démo : demo@onlychat.app / demo1234
"""
import random
from datetime import datetime, timedelta

from .auth import hash_password
from .database import Base, SessionLocal, engine
from .models import (Agency, Contact, Conversation, Media, Membership, Message,
                     Sale, Tag, TelegramAccount, User)


def run():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    owner = User(email="demo@onlychat.app", name="Maxence", password_hash=hash_password("demo1234"))
    chatter = User(email="chatter@onlychat.app", name="Unik", password_hash=hash_password("demo1234"))
    db.add_all([owner, chatter])
    db.flush()

    agency = Agency(name="ALPHA Agency", timezone="Europe/Paris")
    db.add(agency)
    db.flush()

    m_owner = Membership(user_id=owner.id, agency_id=agency.id, role="owner")
    m_chatter = Membership(user_id=chatter.id, agency_id=agency.id, role="chatter")
    db.add_all([m_owner, m_chatter])
    db.flush()

    account = TelegramAccount(
        agency_id=agency.id, label="Ashley", status="connected", tg_user_id=7697191196,
        account_notes="Persona : Ashley, 23 ans, étudiante. Ton joueur, tutoiement. Push PPV après 5 messages.",
    )
    db.add(account)
    db.flush()

    tags = [
        Tag(account_id=account.id, name="TW", color="#38bdf8"),
        Tag(account_id=account.id, name="SPENDER", color="#22c55e"),
        Tag(account_id=account.id, name="WHALE", color="#8b5cf6"),
    ]
    db.add_all(tags)
    db.flush()

    # Vault (offres Dropfan)
    medias = []
    for i in range(1, 8):
        price = random.choice([0, 0, 10, 15, 20, 30])
        medias.append(Media(
            account_id=account.id, folder=random.choice(["All media", "Script 1", "Script 2"]),
            kind="photo", filename=f"20260330_19{i:04d}.jpg", filepath="",
            notes=f"Set {i}", price=price,
            dropfan_url=f"https://dropfan.com/ashley/ppv/{1000+i}" if price else None,
        ))
    db.add_all(medias)
    db.flush()

    names = [
        ("Introvert Person", "Totoymola1984", "Philippines", True),
        ("K.A. Ordoñez", "kaord", "Mexico", False),
        ("Anthony", "anth_x", "USA", False),
        ("Dennis Rolle", "drolle", "UK", False),
        ("Emilien GRENOT", "egrenot", "France", True),
        ("Gilbert Gonzales", "ggon", "USA", False),
        ("Marc T.", "marct", "Canada", False),
        ("David L.", "davidl", "Germany", True),
    ]
    fan_msgs = [
        "Hey are you there?", "I really like your last pic 😍", "When is the next drop?",
        "Can I get a preview?", "You're so beautiful", "Just unlocked your pack!",
        "What are you doing right now?", "I have something to tell you",
    ]
    now = datetime.utcnow()
    for idx, (name, uname, country, prem) in enumerate(names):
        spent = random.choice([0, 0, 10, 25, 60, 120])
        tag_ids = ""
        if spent >= 100:
            tag_ids = str(tags[2].id)
        elif spent > 0:
            tag_ids = str(tags[1].id)
        contact = Contact(
            account_id=account.id, tg_peer_id=1000 + idx, display_name=name, username=uname,
            country=country, is_premium=prem, total_spent=spent, tag_ids=tag_ids,
            occupation=random.choice(["Unknown", "Engineer", "Trader", "Student"]),
        )
        db.add(contact)
        db.flush()

        conv = Conversation(
            account_id=account.id, contact_id=contact.id,
            last_message_at=now - timedelta(minutes=idx * 17),
            unread_count=random.choice([0, 0, 1, 2]),
            needs_reply=idx % 3 == 0, pinned=idx == 0,
        )
        db.add(conv)
        db.flush()

        history = []
        for j in range(random.randint(4, 12)):
            incoming = j % 2 == 0
            history.append(Message(
                conversation_id=conv.id, direction="in" if incoming else "out",
                body=random.choice(fan_msgs) if incoming else "Hey you 😘 tell me more...",
                sent_by_membership_id=None if incoming else m_chatter.id,
                created_at=now - timedelta(minutes=idx * 17 + (12 - j) * 3),
            ))
        db.add_all(history)
        conv.last_message_preview = history[-1].body[:120]

        # Ventes pour les spenders
        if spent > 0:
            n = max(1, int(spent // 20))
            for _ in range(n):
                db.add(Sale(
                    account_id=account.id, conversation_id=conv.id, membership_id=m_chatter.id,
                    kind="ppv", amount=spent / n, source="dropfan",
                    created_at=now - timedelta(days=random.randint(0, 20)),
                ))

    db.commit()
    db.close()
    print("Seed OK — login: demo@onlychat.app / demo1234")


if __name__ == "__main__":
    run()
