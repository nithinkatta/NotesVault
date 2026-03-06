## AI Notes Vault

Full-stack notes app with FastAPI backend and React + Vite frontend. Supports note CRUD, file uploads (local or S3 via presigned URLs), and AI helpers for summarization, OCR, and transcription using OpenAI.

### Tech Stack
- Backend: FastAPI, MongoDB (Motor), Pydantic Settings, HTTPX, OpenAI SDK
- Frontend: React, TypeScript, Vite
- Storage: MongoDB for notes; uploads served locally or via S3 presigned URLs

### Quick Start
1) Prereqs: Python 3.11+, Node 18+.  
2) Backend
```
cd backend
python -m venv .venv
.venv/Scripts/activate  # or source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# set MONGO_URI="mongodb://localhost:27017"
# set OPENAI_API_KEY=...
# optional: docker run -d -p 27017:27017 --name mongo mongo:6
uvicorn app.main:app --reload
```
3) Frontend
```
cd frontend
npm install
npm run dev
```

### Configuration
Backend settings come from environment or `.env`:
- `MONGO_URI` (e.g., `mongodb://localhost:27017`)
- `MONGO_DB` (default `notes`)
- `MONGO_COLLECTION` (default `notes`)
- `OPENAI_API_KEY` (required for AI routes)
- `OPENAI_MODEL` (defaults to `gpt-4o-mini`)
- `USE_LOCAL_UPLOADS` (default True). Set False to use S3 for uploads.
- `AWS_REGION`, `S3_BUCKET` (when S3 uploads are enabled)
- `ALLOWED_ORIGINS` (CORS whitelist)
- Optional local Mongo UI: MongoDB Compass → connect with `mongodb://localhost:27017`.

### API Overview
- `GET /health` – liveness check.
- Notes (`/notes`): list, create, get, update, delete (persisted in MongoDB).
- Storage (`/notes/presign`, `/notes/upload/{key}`): presign S3 uploads; local upload sink when `use_local_uploads=True`.
- AI (`/ai/summarize`, `/ai/ocr`, `/ai/transcribe`): summarize text, OCR from image URL, transcribe audio URL. Optional `note_id` patches the note with results.

### FastAPI Utilization
- `FastAPI` app with `APIRouter` modules for `notes` and `ai`.
- Dependency Injection (`Depends`): settings, Mongo collection (Motor client), note repository.
- Request/response models: Pydantic schemas validate payloads and serialize responses.
- Async I/O: Mongo access via Motor; AI calls via OpenAI SDK; HTTPX for fetches.
- Middleware: CORS configured from settings.
- Static mount `/static` serves uploaded files when in local mode.
- Startup event: ensures Mongo indexes (`note_id` unique, `owner_id`) before serving.

### Data Flow
```mermaid
flowchart TD
    User --> UI[Frontend (React/Vite)]
    UI -->|HTTPS JSON| API[FastAPI app]

    subgraph REST
      API --> NotesRouter[/Routes: GET/POST/PATCH/DELETE /notes/]
      NotesRouter -->|Pydantic validation + Depends| Repo[NoteRepository (Motor)]
      Repo --> MongoDB[(MongoDB)]
      MongoDB --> UI
    end

    subgraph Uploads
      API --> Presign[/Route: POST /notes/presign/]
      Presign --> Storage[S3 presigned URL or Local /static]
      Storage --> UI
      API --> Upload[/Route: PUT /notes/upload/{key}/ (local mode)/]
    end

    subgraph AI
      API --> AIRouter[/Routes: /ai/summarize · /ai/ocr · /ai/transcribe/]
      AIRouter --> OpenAI[OpenAI API]
      OpenAI --> UI
      AIRouter --> Repo
    end
```

### Running with Remote Storage (optional)
- Set `USE_LOCAL_UPLOADS=false` and configure AWS creds/roles.
- Uploads use S3 presigned URLs; notes stay in MongoDB.

### Development Notes
- Keep secrets in environment variables; `.gitignore` excludes env/venv/node_modules.
- Frontend dev server runs on `http://localhost:5173`; backend default `http://localhost:8000`.
