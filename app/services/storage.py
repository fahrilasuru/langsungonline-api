from uuid import uuid4
from fastapi import HTTPException, UploadFile
from services.supabase import supabase

BUCKET = "preview-files"
MAX_FILE_SIZE = 20 * 1024 * 1024
MAX_TOTAL_SIZE = 50 * 1024 * 1024  # jumlah semua berkas dalam satu permintaan
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
EXTENSION = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "application/pdf": ".pdf"}
SIGNED_URL_TTL = 60 * 60 * 24  # 24 jam; dibuat ulang setiap preview dibuka


def sniff_mime(content: bytes) -> str | None:
    """Tipe berkas dari isinya (magic bytes), bukan dari header yang dikirim klien."""
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp"
    if b"%PDF-" in content[:1024]:
        return "application/pdf"
    return None


async def upload_file(preview_id: str, file: UploadFile, remaining: int = MAX_TOTAL_SIZE) -> int:
    """Unggah satu berkas dan kembalikan ukurannya (byte), agar pemanggil bisa menghitung total."""
    # Gerbang murah sebelum membaca isi; pemeriksaan sebenarnya memakai magic bytes di bawah.
    if (file.content_type or "") not in ALLOWED_MIME:
        raise HTTPException(status_code=415, detail="Hanya gambar (JPG, PNG, WebP) atau PDF")

    limit = min(MAX_FILE_SIZE, remaining)
    content = await file.read(limit + 1)

    if len(content) > limit:
        if limit < MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="Total ukuran berkas tidak boleh lebih dari 50MB")
        raise HTTPException(status_code=413, detail="File tidak boleh lebih dari 20MB")

    mime = sniff_mime(content)
    if mime not in ALLOWED_MIME:
        raise HTTPException(status_code=415, detail="Isi berkas bukan gambar (JPG, PNG, WebP) atau PDF yang valid")

    file_id = str(uuid4())
    # Ekstensi dari tipe yang terdeteksi, bukan dari nama berkas buatan pengguna.
    storage_path = f"{preview_id}/{file_id}{EXTENSION[mime]}"

    supabase.storage.from_(BUCKET).upload(
        path=storage_path,
        file=content,
        file_options={"content-type": mime},
    )

    try:
        supabase.table("preview_files").insert({
            "id": file_id,
            "preview_id": preview_id,
            "filename": (file.filename or "")[:200],
            "storage_path": storage_path,
            "mime_type": mime,
            "size": len(content),
        }).execute()

    except Exception:
        try:
            supabase.storage.from_(BUCKET).remove([storage_path])
        except Exception:
            print(f"Gagal membersihkan {storage_path}")

        raise

    return len(content)


def download_file(storage_path: str) -> bytes:
    return supabase.storage.from_(BUCKET).download(storage_path)


def signed_url(storage_path: str) -> str:
    res = supabase.storage.from_(BUCKET).create_signed_url(storage_path, SIGNED_URL_TTL)
    return res.get("signedURL") or res.get("signedUrl") or ""
