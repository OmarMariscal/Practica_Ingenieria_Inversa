import logging
import os
import secrets

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/articulos")
TOKEN_TTL_MINUTES = int(os.getenv("TOKEN_TTL_MINUTES", "1440"))
CORS_ORIGINS = [o for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o]

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = secrets.token_urlsafe(48)
    logging.getLogger("uvicorn.error").warning(
        "SECRET_KEY no definida: se generó una efímera; los tokens dejan de valer al reiniciar."
    )
