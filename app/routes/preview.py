import asyncio
import logging
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, File, Form, Header, HTTPException, Request, Response, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import TypeAdapter
from starlette.concurrency import run_in_threadpool

from config import settings
from limiter import limiter
from models.preview import PreviewResponse
from services.compose import compose, file_ids, resolve_files
from services.gemini import normalize_input
from services.storage import MAX_TOTAL_SIZE, download_file, signed_url, upload_file
from services.supabase import supabase

router = APIRouter()
log = logging.getLogger("preview")

MAX_TEXT = 2000
MAX_FILES = 6
PIPELINE_TIMEOUT = 150           # detik untuk normalize + compose
STALE_AFTER = timedelta(minutes=10)  # job yang tidak selesai sampai sini dianggap gagal
_adapter = TypeAdapter(PreviewResponse)


def _valid_id(preview_id: str) -> str:
    """ID preview selalu UUID. Selain itu 404, bukan 500 dari Postgres."""
    try:
        return str(UUID(preview_id))
    except ValueError:
        raise HTTPException(status_code=404, detail="Preview tidak ditemukan")


# ------------------------------------------------------------------ akses data (sinkron; dipanggil lewat threadpool)
def update_status(preview_id: str, status: str, error: str | None = None):
    data = {"status": status}
    if error is not None:
        data["error"] = error
    supabase.table("previews").update(data).eq("id", preview_id).execute()


def _create(preview_id: str, text: str):
    supabase.table("previews").insert({"id": preview_id, "text": text, "status": "uploading"}).execute()


def _claim(preview_id: str) -> bool:
    claim = (
        supabase.table("previews")
        .update({"status": "processing", "error": None})
        .eq("id", preview_id)
        .eq("status", "pending")
        .execute()
    )
    return bool(claim.data)


def _load_inputs(preview_id: str):
    text = supabase.table("previews").select("text").eq("id", preview_id).single().execute().data["text"] or ""
    rows = supabase.table("preview_files").select("*").eq("preview_id", preview_id).execute().data or []

    files, images = [], []
    for r in rows:
        content = download_file(r["storage_path"])
        mime = r["mime_type"] or "application/octet-stream"
        files.append({"content": content, "mime_type": mime})
        if mime.startswith("image/") and len(images) < 4:
            images.append({"id": f"file_{len(images) + 1}", "file_id": r["id"], "content": content, "mime_type": mime})
    return text, files, images


def _save_result(preview_id: str, normalized, result: dict):
    supabase.table("previews").update({
        "status": "completed",
        "template_type": normalized.template.value,
        "normalized_data": normalized.model_dump(mode="json"),
        "content": result,
        "completeness": result.get("completeness") or result["status"],
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", preview_id).execute()


def _file_urls(preview_id: str, content: dict) -> dict[str, str]:
    """URL bertanda tangan hanya untuk berkas yang benar-benar dirujuk isi preview."""
    ids = file_ids(content)
    if not ids:
        return {}
    rows = (
        supabase.table("preview_files").select("id,storage_path")
        .eq("preview_id", preview_id).in_("id", list(ids)).execute().data or []
    )
    return {r["id"]: signed_url(r["storage_path"]) for r in rows}


def _is_stale(row: dict) -> bool:
    """Butuh kolom created_at (default now() di Supabase). Tanpa kolom itu, pemeriksaan dilewati."""
    raw = row.get("created_at")
    if not raw:
        return False
    try:
        created = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return False
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - created > STALE_AFTER


# ------------------------------------------------------------------ rute
@router.post("/preview")
@limiter.limit("3/minute;15/hour")
async def prepare(
    request: Request,
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
    await run_in_threadpool(_create, preview_id, text)

    try:
        remaining = MAX_TOTAL_SIZE
        for file in files:
            remaining -= await upload_file(preview_id, file, remaining)

        await run_in_threadpool(update_status, preview_id, "pending")

    except HTTPException as exc:  # berkas ditolak (tipe atau ukuran): teruskan pesannya apa adanya
        await run_in_threadpool(update_status, preview_id, "failed", str(exc.detail))
        raise

    except Exception as exc:
        log.exception("Upload gagal")
        await run_in_threadpool(update_status, preview_id, "failed", str(exc))
        raise HTTPException(status_code=500, detail="Gagal upload")

    background.add_task(run_pipeline, preview_id)

    # Formulir di landing memanggil dengan fetch dan meminta JSON; form HTML biasa tetap dialihkan (303).
    if "application/json" in (request.headers.get("accept") or ""):
        return JSONResponse({"id": preview_id, "status": "processing"}, status_code=201)

    # Halaman preview ada di frontend, bukan di API ini.
    return RedirectResponse(
        url=f"{settings.frontend_url.rstrip('/')}/preview/{preview_id}",
        status_code=303,
    )


@router.get("/preview/{preview_id}", response_model=PreviewResponse, response_model_exclude_none=True)
def load(preview_id: str, response: Response):
    """Kontrak yang dibaca frontend: processing | ready | needs_info | declined | failed."""
    preview_id = _valid_id(preview_id)
    res = supabase.table("previews").select("*").eq("id", preview_id).maybe_single().execute()
    row = res.data if res else None  # maybe_single bisa mengembalikan None bila tidak ada baris

    if not row:
        raise HTTPException(status_code=404, detail="Preview tidak ditemukan")

    status = row["status"]
    if status in ("uploading", "pending", "processing"):
        response.headers["Cache-Control"] = "no-store"
        if _is_stale(row):  # proses mati di tengah jalan (restart server, dsb.): hentikan polling di frontend
            update_status(preview_id, "failed", "Waktu pemrosesan habis")
            return {"status": "failed", "job_id": preview_id}
        return {"status": "processing", "job_id": preview_id}

    content = row.get("content")
    if status != "completed" or not content:
        return {"status": "failed", "job_id": preview_id}

    try:
        data = _adapter.validate_python(resolve_files(content, _file_urls(preview_id, content)))
    except Exception:
        log.exception("CONTRACT ERROR")
        response.headers["Cache-Control"] = "no-store"
        return {"status": "failed", "job_id": preview_id}

    # URL bertanda tangan berlaku 24 jam, jadi hasil boleh dipakai ulang sebentar oleh browser.
    response.headers["Cache-Control"] = "private, max-age=30"
    return data


async def run_pipeline(preview_id: str) -> bool:
    """normalize -> compose -> simpan. Aman dipanggil berulang: hanya satu pemanggil yang berhasil 'mengklaim' pending."""
    if not await run_in_threadpool(_claim, preview_id):
        return False  # sudah diproses, sedang diproses, atau belum selesai diunggah

    try:
        text, files, images = await run_in_threadpool(_load_inputs, preview_id)

        async def work():
            normalized = await normalize_input(text=text, files=files)
            return normalized, await compose(preview_id, text, normalized, images)

        normalized, result = await asyncio.wait_for(work(), timeout=PIPELINE_TIMEOUT)
        await run_in_threadpool(_save_result, preview_id, normalized, result)
        return True

    except Exception as exc:
        log.exception("PROCESSING ERROR")
        message = str(exc) or type(exc).__name__  # TimeoutError tidak punya pesan
        await run_in_threadpool(update_status, preview_id, "failed", message[:500])
        return False


@router.post("/preview/{preview_id}/process")
async def generate(
    preview_id: str,
    force: bool = False,
    x_admin_token: str | None = Header(None),
):
    """Pemicu ulang manual untuk admin. Nonaktif (404) bila ADMIN_TOKEN tidak diatur.
    force=true mengembalikan job yang macet (processing) atau gagal ke antrian sebelum dijalankan."""
    if not settings.admin_token:
        raise HTTPException(status_code=404, detail="Tidak ditemukan")
    if not x_admin_token or not secrets.compare_digest(x_admin_token.encode(), settings.admin_token.encode()):
        raise HTTPException(status_code=403, detail="Tidak diizinkan")

    preview_id = _valid_id(preview_id)
    if force:
        await run_in_threadpool(
            lambda: supabase.table("previews").update({"status": "pending", "error": None})
            .eq("id", preview_id).in_("status", ["processing", "failed"]).execute()
        )
    return {"ok": await run_pipeline(preview_id)}
