from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..services.supabase import supabase

router = APIRouter()

class ContactRequest(BaseModel):
    business_name: str
    business_field: str
    city: str
    social_ref: str | None = None
    goal: str
    whatsapp: str

@router.post("/contact")
async def submit(data: ContactRequest):
    if (
        not data.business_name.strip()
        or not data.business_field.strip()
        or not data.city.strip()
        or not data.goal.strip()
        or not data.whatsapp.strip()
    ):
        raise HTTPException(
            status_code=400,
            detail="Data wajib belum lengkap",
        )

    try:
        supabase.table("pesan_langsung").insert({
            "business_name": data.business_name.strip(),
            "business_field": data.business_field.strip(),
            "city": data.city.strip(),
            "social_ref": data.social_ref.strip() if data.social_ref else None,
            "goal": data.goal.strip(),
            "whatsapp": data.whatsapp.strip(),
        }).execute()

    except Exception as exc:
        print(
            "CONTACT ERROR:",
            type(exc).__name__,
            str(exc),
        )

        raise HTTPException(
            status_code=500,
            detail="Gagal mengirim data",
        )

    return {
        "ok": True,
    }