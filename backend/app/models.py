import uuid
from enum import Enum

from celery import states
from sqlmodel import CheckConstraint, Field, Relationship, SQLModel

youtube_video_link = Field(schema_extra={'pattern': r'^[a-zA-Z0-9_-]{11}$'})


class UserBase(SQLModel):
    name: str = Field(unique=True, index=True, max_length=20)


class UserPublic(UserBase):
    id: uuid.UUID


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    user_summaries: list['UserSummary'] = Relationship(back_populates="user")


class UserRegister(SQLModel):
    name: str = Field(unique=True, index=True, max_length=20)
    password: str = Field(min_length=8, max_length=40)


class TaskStatus(str, Enum):
    PENDING = states.PENDING
    FAILURE = states.FAILURE
    SUCCESS = states.SUCCESS


class VideoView(SQLModel):
    link: str = youtube_video_link
    title: str


class VideoRequest(SQLModel):
    link: str = youtube_video_link
    major_language: str = Field(max_length=5)


class VideoResponse(VideoRequest):
    category: str | None = None
    description: str | None = None
    text: str | None = None
    title: str | None = None


class Video(SQLModel, table=True):
    category: str
    description: str
    link: str | None = Field(default=None, primary_key=True)
    major_language: str
    text: str
    title: str
    summaries: list["Summary"] = Relationship(back_populates="video", cascade_delete=True)


class SummaryBase(SQLModel):
    language: str = Field(max_length=5)
    size: str = Field(schema_extra={'pattern': r'^(small|medium|large)$'})


class SummaryView(SummaryBase):
    text: str


class SummaryRequest(SummaryBase):
    video_link: str = youtube_video_link


class SummaryResponse(SummaryRequest):
    text: str | None = None


class Summary(SummaryView, table=True):
    id: int | None = Field(default=None, primary_key=True)
    video_link: str = Field(foreign_key='video.link', ondelete='CASCADE')

    user_summaries: list['UserSummary'] = Relationship(back_populates="summary", cascade_delete=True)
    video: 'Video' = Relationship(back_populates="summaries")

    __table_args__ = (
        CheckConstraint(
            "size IN ('small', 'medium', 'large')",
            name="valid_size_check"
        ),
    )


class UserSummary(SQLModel, table=True):
    __tablename__ = 'user_summary'

    id: int | None = Field(default=None, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    summary_id: int = Field(foreign_key="summary.id", ondelete='CASCADE')

    user: 'User' = Relationship(back_populates='user_summaries')
    summary: 'Summary' = Relationship(back_populates="user_summaries")


class VideoForLibrary(VideoView):
    summaries: list['SummaryView']


class Library(SQLModel):
    videos: list['VideoForLibrary']


class Message(SQLModel):
    message: str


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None
