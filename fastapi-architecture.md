# FastAPI Architectural Flow and Key Concepts

## High-Level Flow
```mermaid
flowchart TD
client[Client] --> http[HTTP Request]
http --> app[FastAPI App]
app --> deps[Dependency Injection]
deps --> router[Path Operation]
router --> logic[Business Logic]
logic --> resp[Response Serialization]
resp --> middleware[Middleware (logging/CORS)]
middleware --> client
```

1. **HTTP Request** arrives (ASGI server like Uvicorn/Hypercorn).
2. **Routing** matches method + path to a path operation function.
3. **Dependency injection** resolves declared `Depends(...)` (settings, DB session, auth).
4. **Validation/serialization** via Pydantic models for body/query/path data.
5. **Business logic** executes; can call async or sync code.
6. **Response** rendered (JSONResponse by default) and middleware applies (CORS, GZip, etc.).

## Core Building Blocks
- **ASGI app**: `app = FastAPI()` creates the application object.
- **Routers**: `APIRouter` groups related endpoints and can mount prefixes/tags.
- **Path operations**: decorators `@app.get/post/put/patch/delete` map to routes.
- **Dependencies**: `Depends` injects reusable components (DB session, config, auth).
- **Pydantic models**: request/response schemas with validation and serialization.
- **Middleware**: cross-cutting concerns (CORS, auth hooks, logging, compression).
- **Background tasks**: `BackgroundTasks` for fire-and-forget work after response.
- **Events**: `@app.on_event("startup"/"shutdown")` for lifecycle setup/teardown.
- **Static files & mount**: `app.mount("/static", StaticFiles(...))` to serve assets.

## Request Lifecycle (Detailed)
1. **ASGI server** hands the scope to FastAPI.
2. **Middleware stack** runs in order of registration.
3. **Router dispatch** finds the path operation; raises 404 if none.
4. **Dependency resolution**: executed in dependency tree order; cached per-request.
5. **Validation**: request data -> Pydantic models; 422 on validation errors.
6. **Handler execution**: sync functions run in threadpool; async awaited directly.
7. **Response building**: model serialization, status codes, headers; custom Response allowed.
8. **Middleware exit**: response passes back through middleware; sent to client.

## Dependency Injection Patterns
- **Per-request resources**: DB session, current user, settings.
- **Shared singletons**: clients (OpenAI, HTTPX) cached with `lru_cache`.
- **Callable signatures**:
  ```python
  def get_settings():
      return Settings()  # cached with @lru_cache for singleton

  def get_db(settings=Depends(get_settings)):
      db = SessionLocal(settings.db_url)
      try:
          yield db
      finally:
          db.close()
  ```
- **Scopes**: Each request gets fresh non-cached deps; `yield`-based deps support teardown.

## Schemas (Pydantic)
- **Request models**: body (`NoteCreate`), query/path params.
- **Response models**: `response_model=NoteOut` enforces output shape.
- **Validation**: automatic 422 responses on bad input; type coercion where possible.
- **Settings**: `BaseSettings` loads env vars with validation.

## Routers and Modularization
- Use `APIRouter` per domain (e.g., `notes`, `auth`), then `app.include_router(router, prefix="/notes", tags=["notes"])`.
- Supports dependencies at router level (auth guards, shared params).
- Prefixes and tags help organize docs (OpenAPI/Swagger UI).

## Middleware and Cross-Cutting Concerns
- **CORS**: `CORSMiddleware` for browser clients.
- **Logging/Tracing**: custom middleware can add request IDs, timing.
- **Compression**: `GZipMiddleware` for large responses.
- Order matters; middleware wraps the entire request/response lifecycle.

## Error Handling
- **HTTPException**: raise with status and detail to produce clean errors.
- **Validation errors**: generated automatically as 422 with error details.
- **Exception handlers**: `app.exception_handler(ExceptionType)` to customize responses/logging.

## Background and Async Work
- **BackgroundTasks**: attach tasks that run after response is sent.
- **Async I/O**: prefer `async def` for network-bound operations; heavy CPU work should go to workers/tasks.

## Static Files & File Uploads
- Mount static directory: `app.mount("/static", StaticFiles(directory="public"), name="static")`.
- File uploads: use `UploadFile` and `File(...)`; streaming-friendly.

## AuthN/AuthZ Patterns
- **OAuth2 with Password/Bearer**: `OAuth2PasswordBearer` for JWT flows.
- **API keys**: custom dependency reading headers/query.
- **Role checks**: dependency that inspects `current_user` and raises 403.

## Testing
- Use `httpx.AsyncClient` or `fastapi.testclient.TestClient`.
- Override dependencies for test doubles:
  ```python
  app.dependency_overrides[get_db] = fake_db
  ```
- Assertions on status codes, response JSON, and side effects.

## Performance Tips
- Reuse clients (HTTP, DB) with dependency caching.
- Avoid blocking calls in `async def`; offload CPU-heavy tasks.
- Enable `uvicorn --workers N` for CPU-bound parallelism (with caution for shared state).
- Use response_model to avoid over-fetching data.

## Deployment Notes
- Run under a production ASGI server (Uvicorn/Gunicorn with uvicorn workers).
- Set timeouts and limits; configure CORS and HTTPS at the edge (reverse proxy).
- Health checks: lightweight `/health` endpoint; optionally deeper `/ready` checks for DB.

## Minimal Example (Pattern Reference)
```python
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

def get_settings():
    return {"currency": "USD"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/items")
def create_item(item: Item, settings=Depends(get_settings)):
    if item.price < 0:
        raise HTTPException(status_code=400, detail="Price must be positive")
    return {"name": item.name, "price": item.price, "currency": settings["currency"]}
```

---
Use this as a quick reference when designing FastAPI services: start with clear routers, typed schemas, dependency-injected resources, and middleware for cross-cutting concerns, then layer auth, background work, and proper error handling.

## Example End-to-End Architecture (User → FastAPI → DB)

```mermaid
flowchart TD
user[User Browser/App] -->|HTTP/JSON| edgeApi[/API Gateway/Ingress/]
edgeApi --> app[FastAPI App]
app --> mid[Middleware\n(CORS, auth, logging)]
mid --> router[Router & Path Ops]
router --> deps[Dependencies\n(settings, db session, auth)]
deps --> logic[Business Logic\n(services/use-cases)]
logic --> repo[Data Access Layer\n(ORM/queries)]
repo --> db[(Database)]
logic --> ext[External Services\n(AI, storage)]
```

Server (FastAPI) responsibilities in this flow:
- Ingress handling: terminate HTTP at `/health`, `/notes`, etc.
- Routing & validation: match path/method; validate input with Pydantic; return 422 on bad input.
- Dependency wiring: inject settings, DB sessions, current user, and shared clients.
- Middleware concerns: CORS, auth checks, request IDs, logging, compression.
- Business logic orchestration: coordinate repos/services; enforce domain rules.
- Persistence: call repositories/ORM to read/write the database.
- External integrations: call AI/storage/other services as needed.
- Responses & errors: shape response models; raise `HTTPException` for clean errors; emit metrics/logs.
