from sqlalchemy import event
from sqlalchemy.engine.base import Connection
from sqlalchemy.orm import joinedload
from sqlmodel import Session, SQLModel, delete, func, select

from app.core.security import verify_password
from app.models import Summary, User, UserSummary, Video


def create_obj(*, session: Session, obj: SQLModel) -> SQLModel:
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


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


def get_summary(*, session: Session, video_link: str, size: str, language: str) -> Summary | None:
    summary = session.exec(
        select(Summary).where(
            Summary.size == size,
            Summary.language == language,
            Summary.video_link == video_link,
        )
    ).one_or_none()
    return summary


def get_user_with_summary(*, session: Session, user: User, summary: Summary) -> UserSummary | None:
    user_summary = session.exec(
        select(UserSummary).where(
            UserSummary.user_id == user.id,
            UserSummary.summary_id == summary.id
        )
    ).one_or_none()
    return user_summary


def link_user_with_summary(*, session: Session, user: User, summary: Summary) -> UserSummary:
    user_summary = UserSummary(user_id=user.id, summary_id=summary.id)
    session.add(user_summary)
    session.commit()
    session.refresh(user_summary)
    return user_summary


def unlink_user_with_summary(*, session: Session, user_summary: UserSummary) -> None:
    session.delete(user_summary)
    session.commit()


def get_users_summaries_with_video(*, session: Session, user: User) -> list[Summary]:
    summaries_with_video = session.exec(
        select(Summary)
        .join(UserSummary)
        .where(UserSummary.user_id == user.id)
        .options(joinedload(Summary.video))
    ).all()
    return summaries_with_video


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
