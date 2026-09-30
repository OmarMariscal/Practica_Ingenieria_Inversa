from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer, field_validator

from app.models import Article, User


class _In(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore", populate_by_name=True)


class ArticleIn(_In):
    title: str = Field(min_length=1, max_length=150)
    description: str = Field(min_length=1)
    body: str = Field(min_length=1)
    tag_list: list[str] = Field(default_factory=list, alias="tagList")

    @field_validator("tag_list")
    @classmethod
    def _clean_tags(cls, tags: list[str]) -> list[str]:
        clean = list(dict.fromkeys(t.strip() for t in tags if t.strip()))
        if any(len(t) > 50 for t in clean):
            raise ValueError("cada etiqueta admite hasta 50 caracteres")
        return clean


class ArticleEnvelopeIn(_In):
    article: ArticleIn


class RegisterIn(_In):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RegisterEnvelopeIn(_In):
    user: RegisterIn


class LoginIn(_In):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class LoginEnvelopeIn(_In):
    user: LoginIn


class _Out(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


def _iso(dt: datetime) -> str:
    dt = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


class AuthorOut(_Out):
    username: str
    bio: str
    image: str | None
    following: bool = False


class ArticleOut(_Out):
    slug: str
    title: str
    description: str
    body: str
    tag_list: list[str] = Field(alias="tagList")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    favorited: bool = False
    favorites_count: int = Field(0, alias="favoritesCount")
    author: AuthorOut

    @field_serializer("created_at", "updated_at")
    def _timestamps(self, value: datetime) -> str:
        return _iso(value)


class ArticleEnvelope(_Out):
    article: ArticleOut


class UserOut(_Out):
    username: str
    email: str
    bio: str
    image: str | None
    token: str


class UserEnvelope(_Out):
    user: UserOut


def article_envelope(a: Article) -> ArticleEnvelope:
    author = AuthorOut(username=a.author.username, bio=a.author.bio or "", image=a.author.image)
    return ArticleEnvelope(
        article=ArticleOut(
            slug=a.slug,
            title=a.title,
            description=a.description,
            body=a.body,
            tag_list=sorted(t.name for t in a.tags),
            created_at=a.created_at,
            updated_at=a.updated_at,
            author=author,
        )
    )


def user_envelope(u: User, token: str) -> UserEnvelope:
    return UserEnvelope(
        user=UserOut(username=u.username, email=u.email, bio=u.bio or "", image=u.image, token=token)
    )
