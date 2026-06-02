import time
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.database import engine, Base
from app.router import router as patients_router
from app.auth_router import router as auth_router
from app.appointment_router import router as appointments_router
import app.models  # noqa: F401 — registers all models with Base.metadata

FRONTEND = Path(__file__).parent.parent / "frontend"

# ── Simple in-process rate limiter (per IP, sliding window) ──────────────────
# For a national-scale deployment replace with Redis + slowapi.
_rate_buckets: dict[str, list[float]] = defaultdict(list)
_RATE_WINDOW = 60.0  # seconds
_AUTH_PATHS = {"/auth/register", "/auth/login", "/auth/forgot-password"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="Medical Patient Registration", lifespan=lifespan, redoc_url=None)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.middleware("http")
async def rate_limit_auth(request: Request, call_next):
    """Reject excessive requests to auth endpoints from the same IP.
    Set RATE_LIMIT_AUTH=0 to disable (e.g. in tests or behind an external rate limiter).
    """
    limit = settings.RATE_LIMIT_AUTH
    if limit > 0 and request.url.path in _AUTH_PATHS:
        ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        # Evict timestamps outside the window
        _rate_buckets[ip] = [t for t in _rate_buckets[ip] if now - t < _RATE_WINDOW]
        if len(_rate_buckets[ip]) >= limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please wait before trying again."},
                headers={"Retry-After": "60"},
            )
        _rate_buckets[ip].append(now)
    return await call_next(request)


@app.exception_handler(SQLAlchemyError)
async def db_exception_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(status_code=500, content={"detail": "Database error"})


app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(appointments_router)

app.mount("/static", StaticFiles(directory=FRONTEND), name="static")


@app.get("/health", include_in_schema=False)
async def health():
    """Liveness probe for Docker healthcheck and load balancer."""
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(FRONTEND / "index.html")
