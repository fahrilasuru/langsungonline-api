import logging
import re

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from limiter import limiter
from services.supabase import supabase

router = APIRouter()
log = logging.getLogger("contact")

# 8-15 digit, boleh diawali + dan dipisah spasi atau tanda hubung.
_PHONE = re.compile(r"^\+?\d[\d\s\-]{6,18}\d$")


class ContactRequest(BaseModel):
    business_name: str = Field(max_length=120)
    business_field: str = Field(max_length=120)
    city: str = Field(max_length=80)
    social_ref: str | None = Field(None, max_length=200)
    goal: str = Field(max_length=200)
    whatsapp: str = Field(max_length=25)
    # Honeypot: kolom tersembunyi di formulir. Manusia tidak mengisinya, bot biasanya mengisi.
    website: str | None = Field(None, max_length=200)


@router.post("/contact")
@limiter.limit("5/minute;20/hour")
async def submit(request: Request, data: ContactRequest):
    if data.website:  # bot: pura-pura berhasil agar tidak tahu kenapa ditolak
        return {"ok": True}

    if not all(
        v.strip()
        for v in (data.business_name, data.business_field, data.city, data.goal, data.whatsapp)
    ):
        raise HTTPException(status_code=400, detail="Data wajib belum lengkap")

    if not _PHONE.match(data.whatsapp.strip()):
        raise HTTPException(status_code=400, detail="Nomor WhatsApp tidak valid")

    try:
        supabase.table("pesan_langsung").insert({
            "business_name": data.business_name.strip(),
            "business_field": data.business_field.strip(),
            "city": data.city.strip(),
            "social_ref": data.social_ref.strip() if data.social_ref else None,
            "goal": data.goal.strip(),
            "whatsapp": data.whatsapp.strip(),
        }).execute()
    except Exception:
        log.exception("Gagal menyimpan pesan kontak")
        raise HTTPException(status_code=500, detail="Gagal mengirim data")

    return {"ok": True}
