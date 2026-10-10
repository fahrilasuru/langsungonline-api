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
    # --- kategori tambahan (ID Unsplash ditulis dari ingatan: VERIFIKASI sebelum dipakai) ---
    "otomotif_jalan": {"cat": "otomotif", "alt": "Mobil melaju di jalan", "url": _u("photo-1492144534655-ae79c964c9d7")},
    "otomotif_sport": {"cat": "otomotif", "alt": "Mobil terparkir di bawah cahaya sore", "url": _u("photo-1503376780353-7e6692767b70")},
    "otomotif_bengkel": {"cat": "otomotif", "alt": "Mekanik memeriksa kendaraan", "url": _u("photo-1486262715619-67b85e0b08d3")},
    "kecantikan_salon": {"cat": "kecantikan", "alt": "Ruang salon yang rapi", "url": _u("photo-1560066984-138dadb4c035")},
    "kecantikan_rambut": {"cat": "kecantikan", "alt": "Penataan rambut di salon", "url": _u("photo-1522337360788-8b13dee7a37e")},
    "fashion_toko": {"cat": "fashion", "alt": "Toko pakaian dengan rak tertata", "url": _u("photo-1441986300917-64674bd600d8")},
    "fashion_rak": {"cat": "fashion", "alt": "Pakaian tergantung rapi", "url": _u("photo-1445205170230-053b83016050")},
    "kuliner_meja": {"cat": "kuliner", "alt": "Hidangan di atas meja", "url": _u("photo-1504674900247-0877df9cc836")},
    "kesehatan_layanan": {"cat": "kesehatan", "alt": "Tenaga kesehatan melayani pasien", "url": _u("photo-1576091160399-112ba8d25d1d")},
    "pendidikan_kelas": {"cat": "pendidikan", "alt": "Ruang kelas dengan murid belajar", "url": _u("photo-1503676260728-1c00da094a0b")},
    "pertanian_lahan": {"cat": "pertanian", "alt": "Hamparan lahan pertanian", "url": _u("photo-1500382017468-9049fed747ef")},
    "konstruksi_proyek": {"cat": "konstruksi", "alt": "Pekerja di lokasi proyek", "url": _u("photo-1504307651254-35680f356dfd")},
}

# id -> (primary, background, ink, deskripsi untuk model)
PALETTES: dict[str, tuple[str, str, str, str, str, str]] = {
    # id -> (primary, background, ink, accent, font, deskripsi untuk model)
    "hangat": ("#B4552D", "#FFF9F0", "#33221A", "#E8A24C", "serif", "hangat, kopi, kuliner, kerajinan"),
    "segar": ("#2F7D5B", "#F6FBF7", "#1D2B24", "#A3D977", "sans", "segar, alam, kesehatan, tanaman"),
    "tenang": ("#2F5D8A", "#F7FAFC", "#1D2B3A", "#5BB5E0", "sans", "profesional, jasa, pendidikan"),
    "elegan": ("#6B3E5E", "#FBF7FA", "#2A1A25", "#D9A0C2", "serif", "kecantikan, fashion, butik"),
    "cerah": ("#D9822B", "#FFFBF2", "#3A2A12", "#F4C95D", "sans", "ceria, komunitas, acara, anak"),
}

# Ikon Font Awesome yang boleh dipilih model (dipakai sebagai nama kelas di frontend).
ICONS = {
    "mug-hot", "mug-saucer", "utensils", "bread-slice", "cake-candles", "location-dot", "comment", "comment-dots", "tag",
    "layer-group", "camera", "camera-retro", "images", "star", "heart", "calendar-days", "bag-shopping", "basket-shopping",
    "box", "store", "scissors", "palette", "pen-ruler", "handshake", "circle-info", "circle-check", "phone", "headset",
    "envelope", "clock", "gift", "truck", "truck-fast", "leaf", "seedling", "shield-heart", "award", "users", "bolt",
    "lightbulb", "wand-magic-sparkles", "hand-holding-heart", "sun", "book-open", "graduation-cap", "dumbbell", "paw",
    "house", "car", "wrench", "laptop-code", "bullhorn", "chart-line", "globe", "gem", "spa", "music", "rocket", "fire",
    "credit-card", "wallet", "stethoscope",
}
