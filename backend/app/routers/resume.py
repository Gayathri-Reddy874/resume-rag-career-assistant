"""Resume upload and Q&A endpoints."""
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.core.dependencies import verify_api_key
from app.core.exceptions import (
    EmptyDocumentError,
    FileTooLargeError,
    ModelInferenceError,
    NoResumeFoundError,
    UnsupportedFileTypeError,
)
from app.core.logging_config import get_logger
from app.models.schemas import AnswerResponse, QuestionRequest, UploadResponse
from app.services import file_parser, vector_store
from app.services.bedrock_client import generate_answer, get_bedrock_client

router = APIRouter(prefix="/api/v1", tags=["resume"], dependencies=[Depends(verify_api_key)])
logger = get_logger(__name__)


@router.post("/upload_resume", response_model=UploadResponse)
async def upload_resume(user_id: str = Form(...), file: UploadFile = File(...)) -> UploadResponse:  # noqa: B008
    content = await file.read()

    try:
        text = file_parser.extract_text(file, content)
        chunks_indexed = vector_store.add_resume(user_id, text, get_bedrock_client())
    except (UnsupportedFileTypeError, FileTooLargeError, EmptyDocumentError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ModelInferenceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    logger.info("Resume uploaded for user_id=%s (%s)", user_id, file.filename)
    return UploadResponse(message="Resume uploaded and indexed successfully.", filename=file.filename, chunks_indexed=chunks_indexed)


@router.post("/ask_question", response_model=AnswerResponse)
async def ask_question(req: QuestionRequest) -> AnswerResponse:
    try:
        answer = generate_answer(req.user_id, req.question)
    except NoResumeFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ModelInferenceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return AnswerResponse(answer=answer, user_id=req.user_id)
