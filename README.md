# Langsung.Online API

Backend FastAPI untuk Langsung.Online: menerima cerita bisnis (teks + berkas), membuat preview website/kehadiran
digital dengan Gemini, dan menyimpannya di Supabase. Frontend ada di repo `langsungonline` (Astro).

## Arsitektur singkat

```
POST /preview ─► simpan teks + berkas ─► 201 {id, status}
                      │  (Supabase: tabel previews, preview_files; bucket preview-files)
                      ▼  background task (routes/preview.py: run_pipeline)
   1. services/gemini.py   normalize_input   cerita + berkas  ─► NormalizedInput (ringkasan terstruktur)
   2. services/compose.py  compose           ─► Draft (isian datar dari model)
                           assemble          ─► Ready (struktur akhir dan aturan fakta dijaga kode;
                                                 model hanya memilih ID aset dari assets.py)
   3. simpan hasil, status completed/failed
GET /preview/{id} ─► PreviewResponse (models/preview.py): ready | needs_info | processing | declined | failed
```

- Status di tabel `previews`: `uploading → pending → processing → completed | failed`. Job yang menggantung
  lebih dari 10 menit dianggap gagal (`_is_stale`) supaya polling frontend berhenti.
- `GET /preview/{id}` memakai `response_model_exclude_none=True`: bidang `None` **tidak dikirim**.
- File pengguna disajikan lewat signed URL berumur pendek (`services/storage.py`).
- Batas: teks 2000 karakter, maksimal 6 berkas, ukuran total dibatasi di `services/storage.py`.
- Rate limit (slowapi): `/preview` 3/menit dan 15/jam, `/contact` 5/menit dan 20/jam per IP.

| Endpoint | Fungsi |
|---|---|
| `POST /preview` | Buat preview (form-data: `text`, `files`) |
| `GET /preview/{id}` | Ambil status/hasil |
| `POST /preview/{id}/process` | Picu ulang manual, butuh `ADMIN_TOKEN` (nonaktif bila kosong) |
| `POST /contact` | Simpan pesan ke tabel `pesan_langsung` |

### Struktur

```
app/
  main.py          aplikasi, CORS, rate limit
  config.py        pengaturan dari environment
  assets.py        pustaka foto/ikon/palet yang boleh dipilih model
  routes/          preview.py, contact.py
  services/        gemini.py, compose.py, storage.py, supabase.py
  models/          preview.py (kontrak respons), normalized.py
  export_openapi.py  menulis openapi.json untuk generator tipe frontend
```

Kode memakai impor datar (`from config import settings`), jadi **semua perintah dijalankan dari folder `app/`**.

## Menjalankan lokal

Prasyarat: Python 3.12 dan proyek Supabase.

```bash
cd app
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # isi nilai rahasia
uvicorn main:app --reload --port 8000
```

Dengan `DEBUG=true`: dokumentasi di `http://localhost:8000/docs`, `/openapi.json` aktif, dan CORS mengizinkan
`localhost:4321` (frontend). Tanpa `DEBUG`, dokumentasi dimatikan.

### Menyiapkan Supabase

Kode mengharapkan (diturunkan dari pemakaian di kode; sesuaikan dengan skema yang sudah ada di proyek Anda):

- bucket **privat** `preview-files`
- tabel `previews` (kolom antara lain `id`, `text`, `status`, `error`, hasil normalisasi/konten, `created_at`),
  `preview_files` (`id`, `preview_id`, `storage_path`, `mime_type`, ...), dan `pesan_langsung`
  (data formulir kontak)

`SUPABASE_KEY` harus *service role key*; jangan pernah dipakai di browser.

## Variabel environment

| Variabel | Wajib | Bawaan | Keterangan |
|---|---|---|---|
| `SUPABASE_URL` | Ya | | URL proyek Supabase |
| `SUPABASE_KEY` | Ya | | Service role key |
| `GEMINI_KEY` | Ya | | API key Gemini |
| `CONSULT_WHATSAPP` | Ya | | Nomor WhatsApp tim, `62812...` tanpa `+`/spasi |
| `GEMINI_MODEL` | Tidak | `gemini-3.5-flash-lite` | Model yang dipakai kedua tahap |
| `FRONTEND_URL` | Tidak | `https://langsung.online` | Origin frontend untuk CORS |
| `EXTRA_ORIGINS` | Tidak | kosong | Origin tambahan, dipisah koma (staging, preview Vercel) |
| `BEHIND_PROXY` | Tidak | `false` | `true` bila di belakang proxy tepercaya, agar rate limit memakai IP asli. Aktifkan di Railway |
| `ADMIN_TOKEN` | Tidak | kosong | Token endpoint `/preview/{id}/process` |
| `DEBUG` | Tidak | `false` | Aktifkan `/docs`, `/openapi.json`, dan CORS localhost |

## Deploy ke Railway

Repo tidak memuat Dockerfile atau Procfile, jadi pengaturan dilakukan di dashboard:

1. Buat service dari repo GitHub ini.
2. **Settings → Root Directory**: `app` (di situlah `requirements.txt` dan `main.py`).
3. **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. **Variables**: isi semua variabel wajib, serta `FRONTEND_URL` (domain Vercel/produksi) dan `BEHIND_PROXY=true`.
   Biarkan `DEBUG` kosong di produksi.
5. Buat domain publik, lalu isi `API_URL` dan `PUBLIC_API_URL` di Vercel dengan domain itu.

## Kontrak ke frontend

`models/preview.py` adalah sumber kebenaran bentuk respons. Frontend menghasilkan `src/types.ts` dari skemanya:

```bash
cd app && python export_openapi.py      # menulis ../openapi.json (tanpa server dan tanpa rahasia asli)
# lalu di frontend:
OPENAPI_SOURCE=../langsungonline-api/openapi.json pnpm gen:types
```

Ubah model, ekspor ulang, generate ulang, commit kedua repo.
