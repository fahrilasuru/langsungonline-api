from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from routes.contact import router as contact_router
from routes.preview import router as preview_router

app = FastAPI()

origins = {
    "https://langsung.online",
    "https://coba.langsung.online",
    "http://localhost:4321",
    "http://127.0.0.1:4321",
    settings.frontend_url.rstrip("/"),
}
# Tidak memakai cookie, jadi allow_credentials tidak diperlukan.
app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(origins),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(preview_router)
app.include_router(contact_router)
