"""
schemas.py
----------

Pydantic request/response models for the API. Using Pydantic here (rather
than hand-rolled dict validation) keeps the validation layer identical to
what a FastAPI version of this service would use — FastAPI is built on
Pydantic, so this schema module ports over unchanged if the app is later
moved from Flask to FastAPI.
"""

from pydantic import BaseModel, Field, field_validator


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)

    @field_validator("question")
    @classmethod
    def question_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("question must not be blank or whitespace-only")
        return v.strip()


class AskResponse(BaseModel):
    question: str
    answer: str


class ErrorResponse(BaseModel):
    error: str
