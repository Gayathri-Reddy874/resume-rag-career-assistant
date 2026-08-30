import json
from io import BytesIO
from unittest.mock import patch

import pytest
from langchain_core.embeddings import Embeddings

from app.core.exceptions import ModelInferenceError, NoResumeFoundError
from app.services import bedrock_client


class _FakeEmbeddings(Embeddings):
    def embed_documents(self, texts):
        return [[float(len(t))] * 8 for t in texts]

    def embed_query(self, text):
        return [float(len(text))] * 8


def _fake_invoke_response(generation: str):
    body = MagicMockBody(json.dumps({"generation": generation}).encode())
    return {"body": body}


class MagicMockBody:
    def __init__(self, data: bytes):
        self._data = data

    def read(self):
        return self._data


def test_raises_when_no_resume_indexed(fake_bedrock_client):
    with pytest.raises(NoResumeFoundError):
        bedrock_client.generate_answer("no-resume-user", "What are my skills?", fake_bedrock_client)


@patch("app.services.vector_store._get_embeddings", return_value=_FakeEmbeddings())
def test_generate_answer_success(mock_embeddings, fake_bedrock_client):
    from app.services import vector_store

    vector_store.add_resume("user-x", "Proficient in Excel and Power BI.", fake_bedrock_client)
    fake_bedrock_client.invoke_model.return_value = _fake_invoke_response("### Skills\n- Excel\n- Power BI")

    answer = bedrock_client.generate_answer("user-x", "What are my skills?", fake_bedrock_client)
    assert "Excel" in answer


@patch("app.services.vector_store._get_embeddings", return_value=_FakeEmbeddings())
def test_generate_answer_wraps_bedrock_failure(mock_embeddings, fake_bedrock_client):
    from app.services import vector_store

    vector_store.add_resume("user-y", "Skilled in project management.", fake_bedrock_client)
    fake_bedrock_client.invoke_model.side_effect = RuntimeError("throttled")

    with pytest.raises(ModelInferenceError):
        bedrock_client.generate_answer("user-y", "What are my skills?", fake_bedrock_client)
