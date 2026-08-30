"""Pydantic request/response models — the API's data contract."""
from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=128, examples=["gayathri_01"])
    question: str = Field(..., min_length=1, max_length=2000, examples=["What skills should I improve?"])


class AnswerResponse(BaseModel):
    answer: str
    user_id: str


class UploadResponse(BaseModel):
    message: str
    filename: str
    chunks_indexed: int


class HealthResponse(BaseModel):
    status: str
    environment: str


class ErrorResponse(BaseModel):
    detail: str
