from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from config import settings
from limiter import limiter
from routes.contact import router as contact_router
from routes.preview import router as preview_router

# Dokumentasi interaktif hanya saat debug.
docs = {} if settings.debug else {"docs_url": None, "redoc_url": None, "openapi_url": None}
app = FastAPI(**docs)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

origins = {
    "https://langsung.online",
    "https://coba.langsung.online",
    settings.frontend_url.rstrip("/"),
    *(o.strip().rstrip("/") for o in settings.extra_origins.split(",") if o.strip()),
}
if settings.debug:
    origins |= {"http://localhost:4321", "http://127.0.0.1:4321"}

# Tidak memakai cookie, jadi allow_credentials tidak diperlukan.
app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(origins),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Accept"],
)

# Batas kasar ukuran request (6 berkas x 20 MB + overhead). Tetap pasang batas di reverse proxy,
# karena request chunked tanpa Content-Length tidak tertangkap di sini.
MAX_BODY = 55 * 1024 * 1024


@app.middleware("http")
async def guard(request: Request, call_next):
    length = request.headers.get("content-length")
    if length and length.isdigit() and int(length) > MAX_BODY:
        return JSONResponse({"detail": "Permintaan terlalu besar"}, status_code=413)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


app.include_router(preview_router)
app.include_router(contact_router)
