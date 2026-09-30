from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import AppError
from app.models import User
from app.schemas import (
    ArticleEnvelope,
    ArticleEnvelopeIn,
    LoginEnvelopeIn,
    RegisterEnvelopeIn,
    UserEnvelope,
    article_envelope,
    user_envelope,
)
from app.security import create_token
from app.services import ArticleService, AuthService

router = APIRouter(prefix="/api")


def current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> User:
    scheme, _, token = (authorization or "").partition(" ")
    if scheme not in ("Token", "Bearer") or not token.strip():
        raise AppError(401, {"authorization": ["se requiere el encabezado Authorization: Token <jwt>"]})
    return AuthService(db).user_from_token(token.strip())


@router.post("/users", status_code=201, response_model=UserEnvelope)
def register(body: RegisterEnvelopeIn, db: Session = Depends(get_db)):
    u = body.user
    user = AuthService(db).register(u.username, u.email, u.password)
    return user_envelope(user, create_token(user.id))


@router.post("/users/login", response_model=UserEnvelope)
def login(body: LoginEnvelopeIn, db: Session = Depends(get_db)):
    user = AuthService(db).login(body.user.email, body.user.password)
    return user_envelope(user, create_token(user.id))


@router.post("/articles", status_code=201, response_model=ArticleEnvelope)
def create_article(
    body: ArticleEnvelopeIn, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    return article_envelope(ArticleService(db).create(user, body.article))


@router.get("/articles/{slug}", response_model=ArticleEnvelope)
def get_article(slug: str, db: Session = Depends(get_db)):
    return article_envelope(ArticleService(db).get(slug))
