import json

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models import Summary, User, UserCreate
from redis import Redis
from sqlmodel import Session, select


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_user_by_name(*, session: Session, name: str) -> User | None:
    statement = select(User).where(User.name == name)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, name: str, password: str) -> User | None:
    db_user = get_user_by_name(session=session, name=name)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def get_summary_from_db(*, session: Session, video_link: str, size: str, language: str) -> Summary | None:
    summary = session.exec(
        select(Summary).where(
            Summary.size == size,
            Summary.language == language,
            Summary.video_link == video_link,
        )
    ).one_or_none()
    return summary


def get_summary_from_cache(*, cache: Redis, video_link: str, size: str, language: str) -> SummaryPublic | None:
    summary_key = f'{settings.REDIS_PREFIX_SUMMARY} {video_link}-{size}-{language}'
    if summary_value := cache.get(summary_key):
        summary_decode = json.loads(summary_value.decode('utf-8'))
        summary = SummaryPublic.model_validate(
            summary_decode, update={
                'video_link': video_link,
                'size': size,
                'language': language
            }
        )
        return summary
