from unittest.mock import MagicMock, patch

from langchain_core.embeddings import Embeddings

from app.services import vector_store


class _FakeEmbeddings(Embeddings):
    """Deterministic fake embedding model so tests never touch AWS."""

    def embed_documents(self, texts):
        return [[float(len(t))] * 8 for t in texts]

    def embed_query(self, text):
        return [float(len(text))] * 8


@patch("app.services.vector_store._get_embeddings", return_value=_FakeEmbeddings())
def test_add_and_query_resume(mock_embeddings, fake_bedrock_client):
    user_id = "user-123"
    text = "Skilled in Python, SQL, and data visualization. " * 5

    chunks_indexed = vector_store.add_resume(user_id, text, fake_bedrock_client)
    assert chunks_indexed > 0

    context = vector_store.query(user_id, "What are the skills?", fake_bedrock_client)
    assert "Python" in context


@patch("app.services.vector_store._get_embeddings", return_value=_FakeEmbeddings())
def test_query_before_upload_returns_empty(mock_embeddings, fake_bedrock_client):
    context = vector_store.query("brand-new-user", "anything?", fake_bedrock_client)
    assert context == ""


@patch("app.services.vector_store._get_embeddings", return_value=_FakeEmbeddings())
def test_users_are_isolated(mock_embeddings, fake_bedrock_client):
    vector_store.add_resume("user-a", "User A knows Kubernetes and Go.", fake_bedrock_client)
    vector_store.add_resume("user-b", "User B knows Photoshop and Illustrator.", fake_bedrock_client)

    context_a = vector_store.query("user-a", "skills?", fake_bedrock_client)
    assert "Kubernetes" in context_a
    assert "Photoshop" not in context_a
