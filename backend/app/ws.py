"""Hub WebSocket : diffuse les évènements temps réel aux clients d'une agence.

Évènements : message.new, conversation.updated, account.status
"""
import asyncio
import json
from collections import defaultdict

from fastapi import WebSocket


class Hub:
    def __init__(self) -> None:
        self.rooms: dict[int, set[WebSocket]] = defaultdict(set)
        self.loop: asyncio.AbstractEventLoop | None = None

    async def connect(self, agency_id: int, ws: WebSocket) -> None:
        await ws.accept()
        self.rooms[agency_id].add(ws)

    def disconnect(self, agency_id: int, ws: WebSocket) -> None:
        self.rooms[agency_id].discard(ws)

    async def broadcast(self, agency_id: int, event: str, data: dict) -> None:
        payload = json.dumps({"event": event, "data": data}, default=str)
        dead = []
        for ws in self.rooms[agency_id]:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.rooms[agency_id].discard(ws)

    def broadcast_threadsafe(self, agency_id: int, event: str, data: dict) -> None:
        """Appelable depuis les workers Telethon (autre task/thread)."""
        if self.loop is None:
            return
        asyncio.run_coroutine_threadsafe(self.broadcast(agency_id, event, data), self.loop)


hub = Hub()
