from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    app_name: str = "LiveWave TV Backend"
    version: str = "1.1.0"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Upstream wrapper configuration - Primary & Fallback mirrors
    upstream_base_url: str = "http://ver3.yacinelive.com"
    upstream_mirrors: List[str] = [
        "http://ver3.yacinelive.com",
        "http://ver4.yacinelive.com",
        "http://ver2.yacinelive.com",
        "https://yacinelive.com",
        "https://yacineapp.tv",
    ]

    # Supported decryption keys across Yacine TV APK versions
    upstream_key: str = "c!xZj+N9&G@Ev@vw"
    upstream_keys: List[str] = [
        "c!xZj+N9&G@Ev@vw",
        "c!xgh$ Setting$#v11236$>",
        "1234567890123456",
        "yacineapp_2023",
    ]

    upstream_timeout_seconds: float = 5.0
    stream_probe_timeout_seconds: float = 4.0

    # Cache TTL in seconds (default 5 minutes)
    cache_ttl_seconds: int = 300

    # Fallback to verified authorized live streams when upstream is unreachable
    enable_authorized_fallback: bool = True

    # Admin Portal Credentials
    admin_username: str = "admin"
    admin_password: str = "admin1234"
    admin_jwt_secret: str = "livewave-super-secret-admin-key-2026"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()


