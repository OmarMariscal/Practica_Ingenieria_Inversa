# Reimplementación de `POST /api/articles` (FastAPI + React)

Práctica de ingeniería inversa: la funcionalidad se recuperó del repositorio
`Sean-Miningah/realWorld-DjangoRestFramework` (commit `8e4729a`, licencia MIT) y se recreó
**desde la especificación** de [`docs/ESPECIFICACION.md`](docs/ESPECIFICACION.md), sin copiar código ni estructura interna.

## Ejecutar

```bash
docker compose up -d db                      # PostgreSQL 16

cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest                                       # 25 pruebas (usan SQLite en memoria)
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
uvicorn app.main:app --reload                # http://localhost:8000/docs

cd ../frontend
npm install && npm run dev                   # http://localhost:5173 (proxy /api → :8000)
```

`DATABASE_URL` (por defecto `postgresql+psycopg://postgres:postgres@localhost:5432/articulos`),
`SECRET_KEY`, `TOKEN_TTL_MINUTES` y `CORS_ORIGINS` se leen del entorno.

## Validación diferencial contra el original

Levanta el proyecto Django en otro puerto (p. ej. 8080) y compara ambos:

```bash
pip install httpx
python tools/characterize.py --base original=http://localhost:8080 --base nuevo=http://localhost:8000
```

## Estructura

```
backend/app/   api.py (rutas) → services.py (reglas) → repositories.py → models.py (SQLAlchemy)
               schemas.py (contrato), security.py, errors.py, config.py, database.py, main.py
backend/tests/ una prueba por regla de negocio (BR) y decisión de divergencia
frontend/src/  App.jsx (registro/login, formulario, traza HTTP), api.js, styles.css
tools/         characterize.py (casos idénticos contra ambas APIs)
docs/          ESPECIFICACION.md
```
