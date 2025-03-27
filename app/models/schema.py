from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class Token(BaseModel):
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserCreate(BaseModel):
    email: str
    password: str


class UserUpdate(BaseModel):
    first_name: str
    last_name: str


class UserResponse(BaseModel):
    id: int
    first_name: str | None = None
    last_name: str | None = None

    class Config:
        from_attributes = True


class PasswordUpdate(BaseModel):
    password: str


class GenerateRoadmapSchema(BaseModel):
    topic: str
    level: str


class RoadmapResponseSchema(BaseModel):
    id: int
    title: str
    content: str

    class Config:
        from_attributes = True
