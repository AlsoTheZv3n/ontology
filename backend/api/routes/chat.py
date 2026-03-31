"""WebSocket endpoint for the Agent chat."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.routes.agent import run_agent_stream

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def chat_ws(websocket: WebSocket):
    """
    WebSocket endpoint for the Agent.

    Client sends:  {"question": "Which company has the most stars?"}
    Server sends:  {"type": "tool_call",   "name": "rank_objects", "input": {...}}
                   {"type": "tool_result", "name": "rank_objects", "result": {...}}
                   {"type": "text",        "content": "Based on..."}
                   {"type": "done"}
    """
    await websocket.accept()
    pool = websocket.app.state.pool

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            question = data.get("question", "").strip()

            if not question:
                await websocket.send_json({"type": "error", "message": "Empty question"})
                continue

            async for event in run_agent_stream(question, pool):
                await websocket.send_json(event)

    except WebSocketDisconnect:
        logger.info("Chat WebSocket disconnected")
    except Exception as e:
        logger.exception("Chat WebSocket error")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
