# 💼 Resume RAG Career Assistant

[![CI](https://github.com/Gayathri-Reddy874/resume-rag-career-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/Gayathri-Reddy874/resume-rag-career-assistant/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock-FF9900?logo=amazonaws&logoColor=white)](https://aws.amazon.com/bedrock/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A retrieval-augmented Q&A assistant that lets users upload their resume and
ask career questions (skills gaps, role fit, resume improvements) - answers
are grounded in their own document using AWS Bedrock (Titan embeddings +
Llama 3) and FAISS, served via FastAPI with a Streamlit UI.


```
Streamlit UI  -HTTP──▶  FastAPI backend  ──▶  FAISS (per-user index)
                                │
                                ▶  AWS Bedrock (Titan embeddings + Llama 3 70B)
```

---

## Design highlights

Notable engineering choices in this codebase:

| Area | Approach |
|---|---|
| Structure | Layered `core/ services/ routers/ models/` package |
| Config | Centralized `pydantic-settings`, `.env`-driven — no hardcoded URLs or model IDs |
| Errors | Typed exception hierarchy → correct HTTP status codes, structured logging |
| Multi-tenancy | One FAISS index per user (hashed on-disk path), so cross-user leakage is structurally impossible and queries stay fast as users grow |
| Validation | File extension + size checked up front with a clear 400 response |
| Security | Configurable CORS allow-list, optional API-key header |
| Testing | `pytest` suite (14 tests) with mocked Bedrock/embeddings - no AWS calls or costs in CI |
| Ops | Dockerfiles + `docker-compose`, healthchecks, GitHub Actions CI |
| Concurrency | Per-user lock to prevent FAISS read/write races |

## Project layout

```
resume-rag-career-assistant/
├── backend/
│   ├── app/
│   │   ├── core/        # config, logging, exceptions, auth dependency
│   │   ├── services/    # file parsing, vector store, Bedrock client
│   │   ├── routers/     # health, resume endpoints
│   │   ├── models/      # Pydantic request/response schemas
│   │   └── main.py      # FastAPI app + wiring
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app.py            # Streamlit UI
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── .github/workflows/ci.yml
```

## Running locally (without Docker)

**1. Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example ../.env   # fill in AWS credentials
uvicorn app.main:app --reload --port 8000
```

**2. Frontend** (in a second terminal)
```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

Visit `http://localhost:8501` for the UI and `http://localhost:8000/docs`
for interactive API docs (Swagger).

## Running with Docker

```bash
cp .env.example .env   # fill in AWS credentials
docker compose up --build
```

- Frontend: http://localhost:8501
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs

## Configuration

All settings live in `.env` (see `.env.example`) at the project root. Notable ones:

- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_DEFAULT_REGION` - standard AWS credential resolution; on real AWS infrastructure, prefer an IAM role over static keys. `config.py` explicitly loads `.env` into the process environment (via `python-dotenv`) in addition to parsing it into typed settings, since boto3's credential chain reads directly from `os.environ` and won't pick up values that only live inside a pydantic settings object.
- `ALLOWED_ORIGINS` - comma-separated list of origins allowed to call the API. Do not use `*` in production.
- `REQUIRE_API_KEY` / `APP_API_KEY` - turn on a shared-secret header (`X-API-Key`) if the API is reachable from outside your own frontend. This is a minimal stopgap, not a substitute for real auth (OAuth2/JWT) in a multi-tenant production deployment.

## AWS Bedrock prerequisites

You need model access enabled in the AWS Bedrock console for:
- `amazon.titan-embed-text-v1` (embeddings)
- `meta.llama3-70b-instruct-v1:0` (generation)

in whichever region you set as `AWS_DEFAULT_REGION`.

## Testing

```bash
cd backend
pytest -v
```

Tests mock the Bedrock client and embeddings entirely - they run offline,
free, and fast, and are wired into CI (`.github/workflows/ci.yml`) on every
push/PR.

## Known limitations / next steps

- FAISS indexes are stored on local disk - fine for a single instance, but
  won't work across multiple backend replicas without a shared volume or a
  managed vector DB (OpenSearch, pgvector, Pinecone). `vector_store.py` is
  written so swapping the storage backend only touches that one file.
- `PyPDF2` is deprecated upstream in favor of `pypdf`; swapping is a
  drop-in change when convenient.
- The API-key auth is a single shared secret, adequate for a personal
  project or demo but not for multiple end users — replace with real
  per-user auth before handling other people's resumes in production.

## Author

**Mallareddygari Gayathri**

[GitHub](https://github.com/Gayathri-Reddy874)

## License

This project is licensed under the [MIT License](LICENSE).

