from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    supabase_url: str
    supabase_key: str
    gemini_key: str
    gemini_model: str = "gemini-3.5-flash-lite"
    # Alamat frontend (tujuan redirect setelah upload) dan nomor WhatsApp tim Langsung Online.
    frontend_url: str = "https://langsung.online"
    consult_whatsapp: str  # format 62812..., tanpa + atau spasi

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
