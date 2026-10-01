from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.preview import router as preview_router
from .routes.contact import router as contact_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://langsung.online",
        "https://coba.langsung.online",
        "http://localhost:4321",
        "http://127.0.0.1:4321",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(preview_router)
app.include_router(preview_router)
