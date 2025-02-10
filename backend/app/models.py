
import uuid

from sqlmodel import CheckConstraint, Field, Relationship, SQLModel


class UserBase(SQLModel):
    name: str = Field(unique=True, index=True, max_length=20)


class UserPublic(UserBase):
    id: uuid.UUID


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str


class UserRegister(SQLModel):
    name: str = Field(unique=True, index=True, max_length=20)
    password: str = Field(min_length=8, max_length=40)


class VideoBase(SQLModel):
    title: str
    description: str
    category: str
    major_language: str = Field(max_length=5)
    text: str


class Video(VideoBase, table=True):
    link: str | None = Field(default=None, primary_key=True)

    summaries: list["Summary"] = Relationship(back_populates="video", cascade_delete=True)


class SummaryBase(SQLModel):
    video_link: str = Field(foreign_key='video.link', ondelete='CASCADE')
    language: str = Field(max_length=5)
    text: str | None = None
    size: str = Field(regex="^(small|medium|large)$")

    __table_args__ = (
        CheckConstraint(
            "size IN ('small', 'medium', 'large')",
            name="valid_size_check"
        ),
    )


class Summary(SummaryBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    user_summaries: list['UserSummary'] = Relationship(back_populates="summary", cascade_delete=True)
    video: 'Video' = Relationship(back_populates="summaries")


class UserSummary(SQLModel, table=True):
    __tablename__ = 'user_summary'

    id: int | None = Field(default=None, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    summary_id: int = Field(foreign_key="summary.id", ondelete='CASCADE')

    summary: 'Summary' = Relationship(back_populates="user_summaries")


class Message(SQLModel):
    message: str


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None
