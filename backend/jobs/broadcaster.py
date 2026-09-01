"""WebSocket broadcaster for live job progress."""

from __future__ import annotations

import asyncio
import json
from typing import Dict, Set

from fastapi import WebSocket


class JobBroadcaster:
    def __init__(self) -> None:
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(session_id, set()).add(websocket)

    def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        conns = self._connections.get(session_id)
        if conns and websocket in conns:
            conns.discard(websocket)
        if conns is not None and not conns:
            self._connections.pop(session_id, None)

    async def _broadcast_async(self, session_id: str, payload: dict) -> None:
        conns = list(self._connections.get(session_id, set()))
        dead: list[WebSocket] = []
        message = json.dumps(payload)
        for ws in conns:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(session_id, ws)

    def publish(self, session_id: str, job) -> None:
        payload = job.model_dump(mode="json") if hasattr(job, "model_dump") else job
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self._broadcast_async(session_id, payload), self._loop)


job_broadcaster = JobBroadcaster()
