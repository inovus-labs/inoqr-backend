from typing import Any
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    #Database
    DB_DRIVER: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    # Auth & OAuth
    SECRET_KEY: str
    SESSION_COOKIE_NAME: str = "__Host-inoqr_session_id"
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    # Frontend & App
    FRONTEND_URL: str = "http://127.0.0.1:8000"
    DEBUG: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8",extra="ignore")

    def get(self,key:str,default:Any =None)-> Any:
        return getattr(self,key,default)
    def __call__(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

config = Settings()
