"""
AWS Bedrock client factory and answer-generation logic.
"""
import json

import boto3

from app.core.config import get_settings
from app.core.exceptions import ModelInferenceError, NoResumeFoundError
from app.core.logging_config import get_logger
from app.services import vector_store

logger = get_logger(__name__)

_PROMPT_TEMPLATE = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an expert AI career coach. Answer using ONLY the resume context provided.
If the context doesn't contain enough information to answer, say so honestly
instead of guessing.

STRICT FORMAT:
- Use Markdown
- Use ### headings
- Use bullet points
- Add spacing between sections
<|eot_id|>
<|start_header_id|>user<|end_header_id|>
Resume context:
{context}

Question:
{question}
<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>
"""


def get_bedrock_client():
    """Create a boto3 Bedrock Runtime client.

    Not cached at import time so tests can monkeypatch/mock it easily, and
    so credential refresh (e.g. via an assumed role) is picked up naturally.
    """
    return boto3.client("bedrock-runtime", region_name=get_settings().aws_region)


def generate_answer(user_id: str, question: str, bedrock_client=None) -> str:
    """Retrieve resume context for the user and ask the LLM to answer the question.

    Raises:
        NoResumeFoundError: if the user has not uploaded a resume yet.
        ModelInferenceError: if the Bedrock call fails or returns nothing usable.
    """
    settings = get_settings()
    client = bedrock_client or get_bedrock_client()

    context = vector_store.query(user_id, question, client)
    if not context:
        raise NoResumeFoundError("Please upload your resume before asking questions.")

    prompt = _PROMPT_TEMPLATE.format(context=context, question=question)

    try:
        response = client.invoke_model(
            modelId=settings.bedrock_llm_model_id,
            body=json.dumps(
                {
                    "prompt": prompt,
                    "max_gen_len": settings.llm_max_gen_len,
                    "temperature": settings.llm_temperature,
                    "top_p": settings.llm_top_p,
                }
            ),
            contentType="application/json",
            accept="application/json",
        )
        result = json.loads(response["body"].read())
        output = result.get("generation", "").strip()
    except Exception as exc:
        logger.exception("Bedrock invoke_model failed for user_id=%s", user_id)
        raise ModelInferenceError("The AI model failed to generate a response. Please try again.") from exc

    if not output:
        raise ModelInferenceError("The model returned an empty response. Please rephrase your question.")

    return output
