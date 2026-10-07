"""Pustaka aset dan palet. Model hanya memilih ID dari sini; URL dibuat oleh kode.
ID foto Unsplash ditulis dari ingatan: VERIFIKASI sebelum produksi."""

def _u(photo: str) -> str:
    return f"https://images.unsplash.com/{photo}?auto=format&fit=crop&w=900&q=70"

LIBRARY: dict[str, dict] = {
    "kopi_cangkir": {"cat": "kopi", "alt": "Secangkir kopi di atas meja", "url": _u("photo-1495474472287-4d71bcdd2085")},
    "kopi_susu": {"cat": "kopi", "alt": "Kopi susu dalam gelas", "url": _u("photo-1511920170033-f8396924c348")},
    "kopi_biji": {"cat": "kopi", "alt": "Biji kopi sangrai", "url": _u("photo-1447933601403-0c6688de566e")},
    "kopi_kedai": {"cat": "kopi", "alt": "Suasana kedai kopi", "url": _u("photo-1554118811-1e0d58224f24")},
    "kopi_roti": {"cat": "makanan", "alt": "Sajian roti dan kopi", "url": _u("photo-1504754524776-8f4f37790ca0")},
    "kerja_tim": {"cat": "jasa", "alt": "Tim sedang berdiskusi", "url": _u("photo-1522202176988-66273c2fd55f")},
    "kerja_laptop": {"cat": "jasa", "alt": "Laptop di meja kerja", "url": _u("photo-1498050108023-c5249f4df085")},
    "kerja_meja": {"cat": "jasa", "alt": "Rekan kerja di depan laptop", "url": _u("photo-1519389950473-47ba0277781c")},
    "kerja_rapat": {"cat": "jasa", "alt": "Rapat bersama klien", "url": _u("photo-1542744173-8e7e53415bb0")},
    "komunitas_kumpul": {"cat": "komunitas", "alt": "Sekelompok teman berkumpul", "url": _u("photo-1529156069898-49953e39b3ac")},
    "komunitas_ngobrol": {"cat": "komunitas", "alt": "Teman-teman mengobrol bersama", "url": _u("photo-1511632765486-a01980e01a18")},
    "acara_ruang": {"cat": "acara", "alt": "Peserta acara di ruang pertemuan", "url": _u("photo-1540575467063-178a50c2df87")},
    "acara_belajar": {"cat": "acara", "alt": "Peserta belajar bersama", "url": _u("photo-1523580494863-6f3031224c94")},
}

# id -> (primary, background, ink, deskripsi untuk model)
PALETTES: dict[str, tuple[str, str, str, str]] = {
    "hangat": ("#B4552D", "#FFF9F0", "#33221A", "hangat, kopi, kuliner, kerajinan"),
    "segar": ("#2F7D5B", "#F6FBF7", "#1D2B24", "segar, alam, kesehatan, tanaman"),
    "tenang": ("#2F5D8A", "#F7FAFC", "#1D2B3A", "profesional, jasa, pendidikan"),
    "elegan": ("#6B3E5E", "#FBF7FA", "#2A1A25", "kecantikan, fashion, butik"),
    "cerah": ("#D9822B", "#FFFBF2", "#3A2A12", "ceria, komunitas, acara, anak"),
}

# Ikon Font Awesome yang boleh dipilih model (dipakai sebagai nama kelas di frontend).
ICONS = {"mug-hot", "utensils", "location-dot", "comment", "tag", "layer-group", "camera", "images", "star", "heart",
         "calendar-days", "bag-shopping", "scissors", "palette", "handshake", "circle-info", "phone", "clock", "gift", "truck"}
