from uuid import uuid4
from fastapi import HTTPException, UploadFile
from services.supabase import supabase

BUCKET = "preview-files"
MAX_FILE_SIZE = 20 * 1024 * 1024
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
SIGNED_URL_TTL = 60 * 60 * 24  # 24 jam; dibuat ulang setiap preview dibuka

async def upload_file(preview_id: str, file: UploadFile):
    if (file.content_type or "") not in ALLOWED_MIME:
        raise HTTPException(status_code=415, detail="Hanya gambar (JPG, PNG, WebP) atau PDF")

    file_id = str(uuid4())
    content = await file.read(MAX_FILE_SIZE + 1)

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File tidak boleh lebih dari 20MB")

    extension = ""
    if "." in file.filename:
        extension = "." + file.filename.rsplit(".", 1)[1].lower()

    storage_path = f"{preview_id}/{file_id}{extension}"

    supabase.storage.from_(BUCKET).upload(
        path=storage_path,
        file=content,
        file_options={"content-type": file.content_type or "application/octet-stream"},
    )

    try:
        supabase.table("preview_files").insert({
            "id": file_id,
            "preview_id": preview_id,
            "filename": file.filename,
            "storage_path": storage_path,
            "mime_type": file.content_type,
            "size": len(content),
        }).execute()

    except Exception:
        try:
            supabase.storage.from_(BUCKET).remove([storage_path])
        except Exception:
            print(f"Gagal membersihkan {storage_path}")

        raise

def download_file(storage_path: str) -> bytes:
    return supabase.storage.from_(BUCKET).download(storage_path)

def signed_url(storage_path: str) -> str:
    res = supabase.storage.from_(BUCKET).create_signed_url(storage_path, SIGNED_URL_TTL)
    return res.get("signedURL") or res.get("signedUrl") or ""
