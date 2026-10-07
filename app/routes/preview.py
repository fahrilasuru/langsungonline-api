from datetime import datetime, timezone
from uuid import uuid4
from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import RedirectResponse
from pydantic import TypeAdapter

from ..config import settings
from ..models.preview import PreviewResponse
from ..services.compose import compose, resolve_files
from ..services.gemini import normalize_input
from ..services.storage import download_file, signed_url, upload_file
from ..services.supabase import supabase

router = APIRouter()

MAX_TEXT = 2000
MAX_FILES = 6
_adapter = TypeAdapter(PreviewResponse)


@router.post("/preview")
async def prepare(
    background: BackgroundTasks,
    text: str = Form(""),
    files: list[UploadFile] = File(default=[]),
):
    text = text.strip()[:MAX_TEXT]
    files = [f for f in files if f.filename]

    if not text and not files:
        raise HTTPException(status_code=400, detail="Ceritakan sedikit tentang usaha Anda")
    if len(files) > MAX_FILES:
        raise HTTPException(status_code=400, detail=f"Maksimal {MAX_FILES} berkas")

    preview_id = str(uuid4())

    supabase.table("previews").insert({
        "id": preview_id,
        "text": text,
        "status": "uploading",
    }).execute()

    try:
        for file in files:
            await upload_file(preview_id, file)

        update_status(preview_id, "pending")

    except HTTPException as exc:  # berkas ditolak (tipe atau ukuran): teruskan pesannya apa adanya
        update_status(preview_id, "failed", str(exc.detail))
        raise

    except Exception as exc:
        update_status(preview_id, "failed", str(exc))
        raise HTTPException(status_code=500, detail="Gagal upload")

    background.add_task(run_pipeline, preview_id)

    # Halaman preview ada di frontend, bukan di API ini.
    return RedirectResponse(
        url=f"{settings.frontend_url.rstrip('/')}/preview/{preview_id}",
        status_code=303,
    )


def update_status(preview_id: str, status: str, error: str | None = None):
    data = {"status": status}
    if error is not None:
        data["error"] = error
    supabase.table("previews").update(data).eq("id", preview_id).execute()


def _file_urls(preview_id: str) -> dict[str, str]:
    rows = supabase.table("preview_files").select("id,storage_path").eq("preview_id", preview_id).execute().data or []
    return {r["id"]: signed_url(r["storage_path"]) for r in rows}


@router.get("/preview/{preview_id}", response_model=PreviewResponse, response_model_exclude_none=True)
def load(preview_id: str):
    """Kontrak yang dibaca frontend: processing | ready | needs_info | declined | failed."""
    res = supabase.table("previews").select("*").eq("id", preview_id).maybe_single().execute()
    row = res.data if res else None  # maybe_single bisa mengembalikan None bila tidak ada baris

    if not row:
        raise HTTPException(status_code=404, detail="Preview tidak ditemukan")

    status = row["status"]
    if status in ("uploading", "pending", "processing"):
        return {"status": "processing", "job_id": preview_id}

    content = row.get("content")
    if status != "completed" or not content:
        return {"status": "failed", "job_id": preview_id}

    try:
        return _adapter.validate_python(resolve_files(content, _file_urls(preview_id)))
    except Exception as exc:
        print("CONTRACT ERROR:", type(exc).__name__, str(exc))
        return {"status": "failed", "job_id": preview_id}


async def run_pipeline(preview_id: str) -> bool:
    """normalize -> compose -> simpan. Aman dipanggil berulang: hanya satu pemanggil yang berhasil 'mengklaim' pending."""
    claim = (
        supabase.table("previews")
        .update({"status": "processing", "error": None})
        .eq("id", preview_id)
        .eq("status", "pending")
        .execute()
    )
    if not claim.data:
        return False  # sudah diproses, sedang diproses, atau belum selesai diunggah

    try:
        text = supabase.table("previews").select("text").eq("id", preview_id).single().execute().data["text"] or ""
        rows = supabase.table("preview_files").select("*").eq("preview_id", preview_id).execute().data or []

        files, images = [], []
        for r in rows:
            content = download_file(r["storage_path"])
            mime = r["mime_type"] or "application/octet-stream"
            files.append({"content": content, "mime_type": mime})
            if mime.startswith("image/") and len(images) < 4:
                images.append({"id": f"file_{len(images) + 1}", "file_id": r["id"], "content": content, "mime_type": mime})

        normalized = await normalize_input(text=text, files=files)
        result = await compose(preview_id, text, normalized, images)

        supabase.table("previews").update({
            "status": "completed",
            "template_type": normalized.template.value,
            "normalized_data": normalized.model_dump(mode="json"),
            "content": result,
            "completeness": result.get("completeness") or result["status"],
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", preview_id).execute()
        return True

    except Exception as exc:
        print("PROCESSING ERROR:", type(exc).__name__, str(exc))
        supabase.table("previews").update({"status": "failed", "error": str(exc)}).eq("id", preview_id).execute()
        return False


@router.post("/preview/{preview_id}/process")
async def generate(preview_id: str):
    """Pemicu ulang manual (pemrosesan utama sudah dijalankan otomatis setelah upload)."""
    return {"ok": await run_pipeline(preview_id)}
