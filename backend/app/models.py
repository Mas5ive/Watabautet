
import uuid

from sqlmodel import Field, SQLModel


class UserBase(SQLModel):
    name: str = Field(unique=True, index=True, max_length=20)


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str


