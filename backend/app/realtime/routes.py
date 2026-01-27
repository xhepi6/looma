from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from app.db import get_db
from app.models import User, Session, Board
from app.realtime.manager import manager

router = APIRouter()


async def get_user_from_cookie(websocket: WebSocket, db: AsyncSession) -> User | None:
    """Get user from session cookie on WebSocket connection."""
    session_id = websocket.cookies.get("sid")
    if not session_id:
        return None

    result = await db.execute(
        select(Session).where(Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session or session.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        return None

    result = await db.execute(
        select(User).where(User.id == session.user_id)
    )
    return result.scalar_one_or_none()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    board_id: int = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for real-time board updates."""
    # Authenticate
    user = await get_user_from_cookie(websocket, db)
    if not user:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    # Verify board exists
    result = await db.execute(
        select(Board).where(Board.id == board_id)
    )
    board = result.scalar_one_or_none()
    if not board:
        await websocket.close(code=4004, reason="Board not found")
        return

    # Connect to room
    await manager.connect(websocket, board_id)

    try:
        while True:
            # Keep connection alive, receive any messages (we don't process client messages in MVP)
            data = await websocket.receive_text()
            # Could handle ping/pong here if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket, board_id)
