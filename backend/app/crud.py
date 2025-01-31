from sqlmodel import Session, select

from app.core.security import get_password_hash
from app.models import User, UserCreate


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


