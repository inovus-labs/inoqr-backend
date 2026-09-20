from starlette.config import Config

config = Config(".env")

DB_DRIVER = config("DB_DRIVER")
DB_USER = config("DB_USER")
DB_PASSWORD = config("DB_PASSWORD")
DB_HOST = config("DB_HOST")
DB_PORT = config("DB_PORT", cast=int)
DB_NAME = config("DB_NAME")
SESSION_COOKIE_NAME = "__Host-inoqr_session_id"
