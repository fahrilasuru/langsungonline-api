from fastapi import Request
from slowapi import Limiter

from config import settings


def client_ip(request: Request) -> str:
    """IP klien untuk rate limit.

    Di balik reverse proxy (Railway, Render, Fly, Nginx, dll.) request.client.host adalah IP proxy,
    sehingga semua pengunjung dianggap satu orang. Aktifkan BEHIND_PROXY=true bila itu kasusnya;
    entri TERAKHIR X-Forwarded-For adalah yang ditambahkan proxy tepercaya (entri awal bisa dipalsukan klien).
    """
    if settings.behind_proxy:
        fwd = request.headers.get("x-forwarded-for", "")
        if fwd:
            return fwd.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=client_ip)
