import logging
import time
from collections import defaultdict, deque
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    UserPromptPart,
    TextPart,
)

from app.db import get_db, async_session_maker
from app.models import User, ChatMessage
from app.schemas import ChatMessageSend, ChatMessageResponse
from app.auth.deps import get_current_user
from app.settings import settings
from app.agent import agent, ChatDeps

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])

# In-memory per-user rate limiter
_rate_limits: dict[int, deque] = defaultdict(deque)


def _check_rate_limit(user_id: int) -> bool:
    now = time.time()
    window = _rate_limits[user_id]
    while window and window[0] < now - 60:
        window.popleft()
    if len(window) >= settings.chat_rate_limit:
        return False
    window.append(now)
    return True


def _db_messages_to_history(messages: list[ChatMessage]) -> list[ModelMessage]:
    """Convert DB chat messages to PydanticAI message history format."""
    history: list[ModelMessage] = []
    for msg in messages:
        if msg.role == "user":
            history.append(ModelRequest(parts=[UserPromptPart(content=msg.content)]))
        elif msg.role == "assistant":
            history.append(ModelResponse(parts=[TextPart(content=msg.content)]))
    return history


@router.post("/chat")
async def chat(
    body: ChatMessageSend,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a chat message and receive a streamed response via SSE."""
    if not settings.chat_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat is currently disabled.",
        )

    if not _check_rate_limit(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please wait a moment.",
        )

    # Save user message
    user_msg = ChatMessage(
        user_id=current_user.id,
        role="user",
        content=body.content,
    )
    db.add(user_msg)
    await db.commit()

    # Load recent history (last 20 messages for LLM context)
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(20)
    )
    recent_messages = list(reversed(result.scalars().all()))

    # Build history excluding the current user message (it's the prompt)
    history_messages = recent_messages[:-1] if recent_messages else []
    message_history = _db_messages_to_history(history_messages)

    user_id = current_user.id
    user_content = body.content

    async def generate():
        full_response = ""
        try:
            async with async_session_maker() as agent_db:
                deps = ChatDeps(user_id=user_id, db=agent_db)
                async with agent.run_stream(
                    user_content,
                    deps=deps,
                    message_history=message_history,
                ) as run:
                    async for chunk in run.stream_text(delta=True):
                        full_response += chunk
                        yield f"data: {chunk}\n\n"
        except Exception as e:
            logger.error(f"Chat agent error: {e}", exc_info=True)
            error_msg = "Sorry, something went wrong. Please try again."
            if not full_response:
                yield f"data: {error_msg}\n\n"
                full_response = error_msg

        # Save assistant response
        if full_response:
            try:
                async with async_session_maker() as save_db:
                    assistant_msg = ChatMessage(
                        user_id=user_id,
                        role="assistant",
                        content=full_response,
                    )
                    save_db.add(assistant_msg)
                    await save_db.commit()
            except Exception as e:
                logger.error(f"Failed to save assistant message: {e}")

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/chat/history", response_model=List[ChatMessageResponse])
async def get_chat_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get chat history for the current user."""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.asc())
        .limit(200)
    )
    return result.scalars().all()
