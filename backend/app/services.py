import re
import unicodedata

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import AppError
from app.models import Article, User
from app.repositories import ArticleRepository, UserRepository
from app.schemas import ArticleIn
from app.security import hash_password, read_token, verify_password


def slugify(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def register(self, username: str, email: str, password: str) -> User:
        email = email.lower()
        errors: dict[str, list[str]] = {}
        if self.users.by_email(email):
            errors["email"] = ["ya está registrado"]
        if self.users.by_username(username):
            errors["username"] = ["ya está en uso"]
        if errors:
            raise AppError(409, errors)
        user = self.users.add(User(username=username, email=email, password_hash=hash_password(password)))
        self.db.commit()
        return user

    def login(self, email: str, password: str) -> User:
        user = self.users.by_email(email.lower())
        if not user or not verify_password(password, user.password_hash):
            raise AppError(401, {"credenciales": ["correo o contraseña incorrectos"]})
        return user

    def user_from_token(self, token: str) -> User:
        user_id = read_token(token)
        user = self.users.by_id(user_id) if user_id else None
        if not user:
            raise AppError(401, {"authorization": ["token inválido o expirado"]})
        return user


class ArticleService:
    def __init__(self, db: Session):
        self.db = db
        self.articles = ArticleRepository(db)

    def create(self, author: User, data: ArticleIn) -> Article:
        slug = slugify(data.title)
        if not slug:
            raise AppError(422, {"title": ["debe contener al menos una letra o un número"]})
        if self.articles.by_title(data.title):
            raise AppError(409, {"title": ["ya existe un artículo con este título"]})
        if self.articles.by_slug(slug):
            raise AppError(409, {"title": ["genera un identificador (slug) ya usado por otro artículo"]})
        article = Article(
            author=author, title=data.title, slug=slug, description=data.description, body=data.body
        )
        try:
            self.articles.add(article, data.tag_list)
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise AppError(409, {"title": ["conflicto de unicidad al guardar; intenta de nuevo"]})
        return article

    def get(self, slug: str) -> Article:
        article = self.articles.by_slug(slug)
        if not article:
            raise AppError(404, {"article": ["no encontrado"]})
        return article
