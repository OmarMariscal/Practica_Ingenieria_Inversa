from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Article, Tag, User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def by_username(self, username: str) -> User | None:
        return self.db.scalar(select(User).where(User.username == username))

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user


class ArticleRepository:
    def __init__(self, db: Session):
        self.db = db

    def by_slug(self, slug: str) -> Article | None:
        return self.db.scalar(select(Article).where(Article.slug == slug))

    def by_title(self, title: str) -> Article | None:
        return self.db.scalar(select(Article).where(Article.title == title))

    def add(self, article: Article, tag_names: list[str]) -> Article:
        known = {}
        if tag_names:
            known = {t.name: t for t in self.db.scalars(select(Tag).where(Tag.name.in_(tag_names)))}
        article.tags = [known.get(n) or Tag(name=n) for n in tag_names]
        self.db.add(article)
        self.db.flush()
        return article
