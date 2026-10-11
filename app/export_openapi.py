"""Menulis skema OpenAPI ke berkas JSON tanpa menjalankan server dan tanpa rahasia asli.

    cd app
    python export_openapi.py            # menulis ../openapi.json
    python export_openapi.py out.json   # atau ke path lain

Berkas ini dibaca `npm run gen:types` di frontend (OPENAPI_SOURCE=<path>). Variabel environment
asli, bila ada, tetap dipakai; nilai bawaan di bawah hanya agar import aplikasi tidak gagal.
"""
import json
import os
import sys
from pathlib import Path

for key, value in {
    "SUPABASE_URL": "https://dummy.supabase.co",
    "SUPABASE_KEY": "dummy.dummy.dummy",
    "GEMINI_KEY": "dummy",
    "CONSULT_WHATSAPP": "620000000000",
}.items():
    os.environ.setdefault(key, value)

from main import app  # noqa: E402  (harus setelah environment diisi)

target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "openapi.json"
target.write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print(f"Skema OpenAPI ditulis ke {target}")
