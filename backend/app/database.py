from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import DATABASE_URL

_opts = (
    {"connect_args": {"check_same_thread": False}, "poolclass": StaticPool}
    if DATABASE_URL.startswith("sqlite")
    else {"pool_pre_ping": True}
)
engine = create_engine(DATABASE_URL, **_opts)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    with SessionLocal() as db:
        yield db
