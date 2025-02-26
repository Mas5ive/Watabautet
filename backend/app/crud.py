import json

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models import (Summary, SummaryPublic, User, UserCreate, UserSummary,
                        Video)
from redis import Redis
from sqlalchemy import event
from sqlalchemy.engine.base import Connection
from sqlalchemy.orm import joinedload
from sqlmodel import Session, delete, func, select


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


def create_summary(*, session: Session, summary: SummaryPublic) -> Summary:
    new_summary = Summary.model_validate(summary)
    session.add(new_summary)
    session.commit()
    session.refresh(new_summary)
    return new_summary


def get_user_with_summary(*, session=Session, user=User, summary=Summary) -> UserSummary | None:
    user_summary = session.exec(
        select(UserSummary).where(
            UserSummary.user_id == user.id,
            UserSummary.summary_id == summary.id
        )
    ).one_or_none()
    return user_summary


def link_user_with_summary(*, session=Session, user=User, summary=Summary) -> UserSummary:
    user_summary = UserSummary(user_id=user.id, summary_id=summary.id)
    session.add(user_summary)
    session.commit()
    session.refresh(user_summary)
    return user_summary


def unlink_user_with_summary(*, session=Session, user_summary=UserSummary) -> None:
    session.delete(user_summary)
    session.commit()


def get_users_summaries_with_video(*, session=Session, user=User) -> list[Summary]:
    summaries_with_video = session.exec(
        select(Summary)
        .join(UserSummary)
        .where(UserSummary.user_id == user.id)
        .options(joinedload(Summary.video))
    ).all()
    return summaries_with_video


def get_video_from_cache(*, cache: Redis, video_link: str) -> Video | None:
    video_key = f'{settings.REDIS_PREFIX_VIDEO} {video_link}'
    if video_value := cache.get(video_key):
        video = json.loads(video_value.decode('utf-8'))
        video = Video.model_validate(video, update={'link': video_link})
        return video


@event.listens_for(UserSummary, "after_delete")
def _delete_orphaned_entities_in_db(mapper, connection: Connection, target: UserSummary) -> None:
    """
    Cascade deletes orphaned entities in the DB using the following chain:
    UserSummary(trigger) -> Summary -> Video
    """
    user_summary_count = connection.execute(
        select(func.count()).select_from(UserSummary).
        where(UserSummary.summary_id == target.summary_id)
    ).scalar()

    if user_summary_count:
        return

    connection.execute(delete(Summary).where(Summary.id == target.summary_id))

    summary_count = connection.execute(
        select(func.count()).select_from(Summary).
        where(Summary.video_link == target.summary.video_link)
    ).scalar()

    if summary_count:
        return

    connection.execute(delete(Video).where(Video.link == target.summary.video_link))
