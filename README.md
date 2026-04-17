# Looma

A real-time collaborative task and media management app built for two. Looma combines shared todo boards with movie/TV show tracking, AI-powered chat assistance, automatic translations, and live synchronization across devices.

## Features

### Task Management
- Create, edit, and delete tasks with priorities (low/medium/high), due dates, and notes
- Custom color-coded labels with automatic English translations
- Recurring tasks — daily, weekly, monthly, weekdays, or custom schedules
- Drag-and-drop reordering
- Filter and search across tasks
- Track who created, edited, or completed each task

### Media Tracking
- Track movies and TV shows with statuses: want to watch, watching, watched
- Automatic metadata enrichment via TMDB (year, genre, rating, synopsis, seasons)
- Drag-and-drop reordering

### AI Chat Assistant
- Conversational interface with streaming responses
- Can list, create, update, complete, and delete tasks and media through natural language
- Context-aware — knows your boards, items, and labels
- Supports English and Albanian

### Real-Time Sync
- WebSocket-based live updates across all connected clients
- Changes to tasks, media, and labels broadcast instantly

### Mobile-First PWA
- Installable on mobile and desktop
- Offline support with Workbox caching
- Bottom tab navigation optimized for mobile

### Notifications (Optional)
- Push notifications via [ntfy](https://ntfy.sh)
- Discord webhook integration
- Scheduled reminders for due tasks

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| UI | Radix UI, Framer Motion, dnd-kit, Lucide icons |
| Backend | FastAPI, Python, async/await |
| Database | SQLite (aiosqlite + SQLAlchemy 2.0) |
| Migrations | Alembic |
| AI/LLM | PydanticAI + OpenRouter (Gemini 2.0 Flash) |
| Real-time | WebSockets (FastAPI native) |
| Auth | Session cookies, bcrypt password hashing |
| Infrastructure | Docker, Docker Compose |
| CI/CD | GitHub Actions — auto-deploy on push to main |

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)

### Setup

1. **Clone the repository**

   ```bash
   git clone git@github.com:xhepi6/looma.git
   cd looma
   ```

2. **Create your environment file**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set at minimum:
   - `APP_SECRET_KEY` — a secure random string

   Optional integrations:
   - `OPENROUTER_API_KEY` — enables AI chat and automatic translations
   - `TMDB_API_KEY` — enables movie/TV metadata enrichment
   - `NTFY_USERNAME` / `NTFY_PASSWORD` — enables push notifications
   - `DISCORD_WEBHOOK_URL` — enables Discord notifications

3. **Start the app**

   ```bash
   docker compose -f docker-compose.local.yml up -d --build
   ```

4. **Open in browser**

   - Frontend: [http://localhost:5173](http://localhost:5173)
   - API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

   Two default users are seeded on first run:
   - `alice` / `password123`
   - `bob` / `password123`

   (Configurable via `SEED_USER_*` env vars.)

### Common Commands

All commands run through Docker Compose:

```bash
# View logs
docker compose -f docker-compose.local.yml logs -f api
docker compose -f docker-compose.local.yml logs -f web

# Run backend commands
docker compose -f docker-compose.local.yml exec api alembic upgrade head
docker compose -f docker-compose.local.yml exec api python -m app.seed_test_data

# Run frontend commands
docker compose -f docker-compose.local.yml exec web npm install <package>

# Rebuild after dependency changes
docker compose -f docker-compose.local.yml up -d --build

# Stop everything
docker compose -f docker-compose.local.yml down
```

## Project Structure

```
looma/
├── backend/
│   ├── app/
│   │   ├── agent/          # AI chat assistant (PydanticAI)
│   │   ├── api/            # REST API endpoints
│   │   ├── auth/           # Authentication routes & utilities
│   │   ├── db/             # Database engine & initialization
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── realtime/       # WebSocket connection manager
│   │   ├── schemas/        # Pydantic request/response models
│   │   ├── services/       # Business logic (translation, TMDB, notifications)
│   │   ├── main.py         # FastAPI app entry point
│   │   └── settings.py     # Environment configuration
│   ├── alembic/            # Database migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── hooks/          # Custom React hooks (auth, chat, websocket, theme)
│   │   ├── lib/            # API client, utilities, color helpers
│   │   └── pages/          # Page components (Board, Media, Chat, Settings)
│   ├── public/             # PWA icons and static assets
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml          # Production
├── docker-compose.local.yml    # Development
└── .env.example
```

## API Overview

| Endpoint | Description |
|----------|-------------|
| `POST /api/auth/login` | Login |
| `GET /api/auth/me` | Current user |
| `PATCH /api/auth/me/password` | Change password |
| `GET /api/boards` | List boards |
| `GET /api/boards/{id}/items` | List tasks on a board |
| `POST /api/boards/{id}/items` | Create task |
| `PATCH /api/items/{id}` | Update task |
| `DELETE /api/items/{id}` | Delete task |
| `GET /api/boards/{id}/labels` | List labels |
| `POST /api/boards/{id}/labels` | Create label |
| `GET /api/boards/{id}/media` | List media items |
| `POST /api/boards/{id}/media` | Create media item |
| `PATCH /api/media/{id}` | Update media item |
| `DELETE /api/media/{id}` | Delete media item |
| `POST /api/chat` | Send chat message (SSE streaming) |
| `GET /api/chat/history` | Chat history |
| `WS /ws` | WebSocket for real-time board updates |
| `GET /api/health` | Health check |

Full interactive docs available at `/docs` (Swagger UI) when the API is running.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `APP_SECRET_KEY` | Yes | Secret key for session signing |
| `API_PORT` | No | Backend port (default: 8000) |
| `WEB_PORT` | No | Frontend port (default: 5173) |
| `CORS_ORIGINS` | No | Allowed CORS origins |
| `SEED_USER_1_USERNAME` | No | First user's username (default: alice) |
| `SEED_USER_1_PASSWORD` | No | First user's password (default: password123) |
| `SEED_USER_2_USERNAME` | No | Second user's username (default: bob) |
| `SEED_USER_2_PASSWORD` | No | Second user's password (default: password123) |
| `OPENROUTER_API_KEY` | No | Enables AI chat and translations |
| `TRANSLATION_MODEL` | No | LLM model for translations (default: gemini-2.0-flash) |
| `TRANSLATION_ENABLED` | No | Toggle translations (default: true) |
| `CHAT_MODEL` | No | LLM model for chat (default: gemini-2.0-flash) |
| `CHAT_ENABLED` | No | Toggle AI chat (default: true) |
| `CHAT_RATE_LIMIT` | No | Chat requests per user per minute (default: 20) |
| `TMDB_API_KEY` | No | Enables movie/TV metadata enrichment |
| `TMDB_ENABLED` | No | Toggle TMDB integration (default: true) |
| `DISCORD_WEBHOOK_URL` | No | Discord notification webhook |
| `NTFY_USERNAME` | No | ntfy authentication username |
| `NTFY_PASSWORD` | No | ntfy authentication password |
| `REMINDER_ENABLED` | No | Toggle scheduled reminders (default: false) |

## Deployment

Production deployment is automated via GitHub Actions. Pushing to `main` triggers:

1. SSH into the production server
2. Pull latest code
3. Rebuild and restart containers with `docker compose up -d --build`
4. Alembic migrations run automatically on API startup
