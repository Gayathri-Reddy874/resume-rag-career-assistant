"""
Vector store management.

Design change from the original prototype: each user gets their OWN FAISS
index on disk (data/vector_store/<hashed_user_id>/) instead of one shared
index that gets filtered by metadata after retrieval. Reasons:

1. Isolation: a shared index means every user's resume text is loaded into
   memory and searched on every query, then filtered — an easy path to
   accidentally leaking one user's data to another if the filter is ever
   forgotten or a similarity match ties on document count. Per-user indexes
   make cross-user leakage structurally impossible.
2. Performance: similarity_search cost grows with total corpus size across
   ALL users, not just the one asking. Per-user indexes keep queries fast
   as the user base grows.
3. Concurrency: a threading.Lock per user_id avoids read/write races when
   FAISS reads/writes its on-disk index, without serializing unrelated users.

For a production deployment beyond a single instance, swap this file's
storage backend for a managed vector DB (e.g. OpenSearch, pgvector,
Pinecone) — the public functions below (`add_resume`, `query`) are the only
integration surface the rest of the app depends on.
"""
import hashlib
import threading
from pathlib import Path

from langchain_community.embeddings import BedrockEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings
from app.core.exceptions import ModelInferenceError
from app.core.logging_config import get_logger

logger = get_logger(__name__)

_locks: dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()


def _lock_for(user_id: str) -> threading.Lock:
    """One lock per user_id, created lazily and reused (double-checked locking)."""
    with _locks_guard:
        if user_id not in _locks:
            _locks[user_id] = threading.Lock()
        return _locks[user_id]


def _user_dir(user_id: str) -> Path:
    # Hash the user_id for the on-disk folder name so arbitrary/unsafe
    # characters in a user-supplied ID can never become a path traversal
    # vector (e.g. user_id="../../etc").
    safe_name = hashlib.sha256(user_id.encode()).hexdigest()[:32]
    path = Path(get_settings().vector_store_dir) / safe_name
    path.mkdir(parents=True, exist_ok=True)
    return path


def _get_embeddings(bedrock_client) -> BedrockEmbeddings:
    return BedrockEmbeddings(client=bedrock_client, model_id=get_settings().bedrock_embedding_model_id)


def add_resume(user_id: str, text: str, bedrock_client) -> int:
    """Chunk, embed, and persist resume text for a given user.

    Returns:
        Number of chunks indexed.
    """
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    chunks = splitter.split_text(text)
    if not chunks:
        return 0

    embeddings = _get_embeddings(bedrock_client)
    index_path = _user_dir(user_id)

    with _lock_for(user_id):
        try:
            if (index_path / "index.faiss").exists():
                db = FAISS.load_local(
                    str(index_path), embeddings, allow_dangerous_deserialization=True
                )
                db.add_texts(chunks)
            else:
                db = FAISS.from_texts(chunks, embeddings)
            db.save_local(str(index_path))
        except Exception as exc:
            logger.exception("Failed to index resume for user_id=%s", user_id)
            raise ModelInferenceError("Failed to generate embeddings for the uploaded resume.") from exc

    logger.info("Indexed %d chunks for user_id=%s", len(chunks), user_id)
    return len(chunks)


def query(user_id: str, question: str, bedrock_client) -> str:
    """Return the top-k most relevant resume chunks for a question, joined as context."""
    index_path = _user_dir(user_id)
    if not (index_path / "index.faiss").exists():
        return ""

    embeddings = _get_embeddings(bedrock_client)

    with _lock_for(user_id):
        try:
            db = FAISS.load_local(
                str(index_path), embeddings, allow_dangerous_deserialization=True
            )
            results = db.similarity_search(question, k=get_settings().retrieval_k)
        except Exception as exc:
            logger.exception("Retrieval failed for user_id=%s", user_id)
            raise ModelInferenceError("Failed to search the resume index.") from exc

    return "\n".join(r.page_content for r in results)
