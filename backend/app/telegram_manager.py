"""Gestion des sessions MTProto (Telethon).

Un client par compte Telegram connecté. Responsable de :
- login par QR code (auth.exportLoginToken)
- import de l'historique (dialogs + messages)
- écoute temps réel (NewMessage) -> persistance + broadcast WebSocket
- envoi de messages (texte / lien Dropfan)

NOTE MVP : Telethon est optionnel au démarrage. Si la lib ou les
identifiants API ne sont pas présents, le CRM tourne en mode "démo"
(données seedées, pas de vrai Telegram). Ça permet de développer et
démontrer l'UI sans risquer un compte réel.
"""
from __future__ import annotations

import asyncio
from typing import Any

from .config import settings

try:
    from telethon import TelegramClient, events
    from telethon.sessions import StringSession
    TELETHON_AVAILABLE = True
except Exception:  # pragma: no cover - lib absente en sandbox
    TELETHON_AVAILABLE = False


class TelegramManager:
    def __init__(self) -> None:
        self.clients: dict[int, Any] = {}          # account_id -> TelegramClient
        self.qr_logins: dict[int, Any] = {}        # account_id -> qr_login en cours
        self._on_message = None                     # callback(account_id, event)

    def set_message_handler(self, cb) -> None:
        self._on_message = cb

    @property
    def ready(self) -> bool:
        return TELETHON_AVAILABLE and settings.TG_API_ID and settings.TG_API_HASH

    def _new_client(self, session_string: str | None = None):
        return TelegramClient(
            StringSession(session_string or ""),
            settings.TG_API_ID,
            settings.TG_API_HASH,
        )

    async def start_qr_login(self, account_id: int) -> dict:
        """Démarre un login QR. Retourne l'URL à encoder en QR côté front."""
        if not self.ready:
            return {"available": False, "reason": "Telethon non configuré (mode démo)"}
        client = self._new_client()
        await client.connect()
        qr = await client.qr_login()
        self.qr_logins[account_id] = (client, qr)
        return {"available": True, "url": qr.url, "expires": qr.expires.isoformat()}

    async def poll_qr_login(self, account_id: int) -> dict:
        """Vérifie si l'utilisateur a scanné le QR. Retourne session_string si OK."""
        entry = self.qr_logins.get(account_id)
        if not entry:
            return {"status": "no_login"}
        client, qr = entry
        try:
            user = await asyncio.wait_for(qr.wait(timeout=1), timeout=2)
        except asyncio.TimeoutError:
            return {"status": "pending"}
        except Exception as e:  # QR expiré, 2FA requise, etc.
            return {"status": "error", "detail": str(e)}
        session_string = client.session.save()
        self.clients[account_id] = client
        self.qr_logins.pop(account_id, None)
        return {
            "status": "connected",
            "session_string": session_string,
            "tg_user_id": user.id,
            "username": user.username,
        }

    async def resume(self, account_id: int, session_string: str) -> bool:
        """Reconnecte un compte à partir de sa session sauvegardée."""
        if not self.ready or not session_string:
            return False
        client = self._new_client(session_string)
        await client.connect()
        if not await client.is_user_authorized():
            return False
        self.clients[account_id] = client
        if self._on_message:
            @client.on(events.NewMessage(incoming=True))
            async def handler(event):  # noqa
                await self._on_message(account_id, event)
        return True

    async def send_message(self, account_id: int, peer_id: int, text: str) -> int | None:
        client = self.clients.get(account_id)
        if client is None:
            return None
        msg = await client.send_message(peer_id, text)
        return msg.id


manager = TelegramManager()
