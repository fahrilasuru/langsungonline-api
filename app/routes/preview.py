from datetime import datetime, timezone
from uuid import uuid4
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from services.supabase import supabase
from services.storage import upload_file, download_file
from services.gemini import normalize_input

router = APIRouter()

@router.post("/preview")
async def prepare(
        text: str = Form(""),
        files: list[UploadFile] = File(default=[]),
):
    preview_id = str(uuid4())
    
    supabase.table("previews").insert({
        "id": preview_id,
        "text": text,
        "status": "uploading",
    }).execute();

    try:
        for file in files:
            if not file.filename:
                continue

            await upload_file(preview_id, file)

        update_status(preview_id, "pending")

    except Exception as exc:
        update_status(preview_id, "failed", str(exc))

        raise HTTPException(
            status_code=500,
            detail="Gagal upload"
        )

    return RedirectResponse(
        url=f"/preview/{preview_id}",
        status_code=303
    )

def update_status(
    preview_id: str,
    status: str,
    errorFeedback: str = None,
):
    data = { "status": status }

    if (errorFeedback is not None):
        data["error"] = errorFeedback

    supabase.table("previews").update(data).eq("id", preview_id).execute()

@router.get("/preview/{preview_id}")
async def load(
    request: Request,
    preview_id: str,
):
    response = (
        supabase
        .table("previews")
        .select("*")
        .eq("id", preview_id)
        .maybe_single()
        .execute()
    )

    preview = response.data

    if not preview:
        raise HTTPException(
            status_code=404,
            detail="Preview tidak ditemukan",
        )

    files_response = (
        supabase
        .table("preview_files")
        .select("*")
        .eq("preview_id", preview_id)
        .execute()
    )

    return {
        "preview": preview,
        "files": files_response.data,
    }

@router.post("/preview/{preview_id}/process")
async def generate(preview_id: str):
    preview_response = (
        supabase
        .table("previews")
        .select("*")
        .eq("id", preview_id)
        .single()
        .execute()
    )

    preview = preview_response.data

    if preview["status"] != "pending":
        print("Preview tidak berstatus pending, skipping")
        return

    supabase.table("previews").update({
        "status": "processing",
        "error": None,
    }).eq("id", preview_id).execute()

    try:
        files_response = (
            supabase
            .table("preview_files")
            .select("*")
            .eq("preview_id", preview_id)
            .execute()
        )

        files = []

        for file_record in files_response.data:
            content = download_file(file_record["storage_path"])

            files.append({
                "content": content,
                "mime_type": file_record["mime_type"] or "application/octet-stream",
            })

        normalized = await normalize_input(
            text=preview["text"] or "",
            files=files,
        )

        print(normalized)

        normalized_data = normalized.model_dump(mode="json")

        supabase.table("previews").update({
            "status": "completed",
            "template_type": normalized.template.value,
            "normalized_data": normalized_data,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", preview_id).execute()

    except Exception as exc:
        print(
            "PROCESSING ERROR:",
            type(exc).__name__,
            str(exc),
        )

        supabase.table("previews").update({
            "status": "failed",
            "error": str(exc),
        }).eq("id", preview_id).execute()

        raise

    return {
        "ok": True,
    }