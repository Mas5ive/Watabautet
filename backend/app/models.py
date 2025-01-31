
import uuid

from sqlmodel import Field, SQLModel


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


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None
