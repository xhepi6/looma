import logging
from datetime import datetime, timezone

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from sqlalchemy import select, func

from app.settings import settings
from app.models import Board, Item, Label, MediaItem
from app.models.item import ItemStatus
from app.agent.context import ChatDeps

logger = logging.getLogger(__name__)

model = OpenAIChatModel(
    settings.chat_model,
    provider=OpenAIProvider(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.openrouter_api_key,
    ),
)

agent = Agent(model=model, deps_type=ChatDeps)


@agent.system_prompt
async def build_system_prompt(ctx: RunContext[ChatDeps]) -> str:
    db = ctx.deps.db
    now = datetime.now(timezone.utc)

    # Gather boards
    result = await db.execute(select(Board).order_by(Board.id))
    boards = result.scalars().all()

    board_sections = []
    for board in boards:
        if board.board_type == "task":
            # Item counts
            total = await db.execute(
                select(func.count(Item.id)).where(Item.board_id == board.id)
            )
            total_count = total.scalar() or 0

            todo = await db.execute(
                select(func.count(Item.id)).where(
                    Item.board_id == board.id, Item.status == ItemStatus.TODO
                )
            )
            todo_count = todo.scalar() or 0

            overdue = await db.execute(
                select(func.count(Item.id)).where(
                    Item.board_id == board.id,
                    Item.status == ItemStatus.TODO,
                    Item.due_at < now,
                    Item.due_at.isnot(None),
                )
            )
            overdue_count = overdue.scalar() or 0

            # Labels
            labels_result = await db.execute(
                select(Label).where(Label.board_id == board.id).order_by(Label.name)
            )
            labels = labels_result.scalars().all()
            label_list = ", ".join(
                f"{l.name} (english: {l.english_name})" if l.english_name else l.name
                for l in labels
            )

            board_sections.append(
                f"- Board '{board.name}' (id={board.id}, type=task): "
                f"{todo_count} todo, {total_count - todo_count} done, {overdue_count} overdue. "
                f"Labels: [{label_list}]"
            )
        elif board.board_type == "media":
            media_count = await db.execute(
                select(func.count(MediaItem.id)).where(MediaItem.board_id == board.id)
            )
            count = media_count.scalar() or 0
            board_sections.append(
                f"- Board '{board.name}' (id={board.id}, type=media): {count} items"
            )

    boards_context = "\n".join(board_sections)

    return f"""You are Looma, a helpful personal assistant for managing tasks and media.
You have access to the user's boards and can create, update, delete, and query items.

Current date/time: {now.strftime("%Y-%m-%d %H:%M UTC")}

Boards:
{boards_context}

Instructions:
- You understand both English and Albanian. Respond in whatever language the user writes in.
- When the user mentions a label name, match it to existing labels (case-insensitive). Use the english translations to help match.
- Before calling delete_item or delete_media, always ask the user to confirm first. Only proceed with deletion after they explicitly say yes.
- For bulk operations affecting multiple items, ask for confirmation first.
- Keep responses concise and helpful. Use short confirmations for simple actions.
- When listing items, format them in a clear, readable way.
- When creating items, default to medium priority unless the user specifies otherwise.
- The user's id is {ctx.deps.user_id}."""


# Import tools to register them on the agent
import app.agent.tools  # noqa: F401, E402
