"""
AI Career Assistant — Streamlit frontend.

Talks to the FastAPI backend over HTTP. Configuration comes from
environment variables so the same code works locally and when deployed
(e.g. backend and frontend on different hosts/containers).
"""
import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
API_KEY = os.getenv("APP_API_KEY", "")
REQUEST_TIMEOUT = 30

st.set_page_config(page_title="Resume RAG Career Assistant", page_icon="💼", layout="wide")


def _headers() -> dict:
    return {"X-API-Key": API_KEY} if API_KEY else {}


def _backend_healthy() -> bool:
    try:
        r = requests.get(f"{API_URL}/health", timeout=5)
        return r.status_code == 200
    except requests.RequestException:
        return False


# ------------------ SESSION STATE ------------------
st.session_state.setdefault("chat", [])
st.session_state.setdefault("resume_uploaded", False)

# ------------------ SIDEBAR ------------------
with st.sidebar:
    st.title("⚙️ Settings")
    user_id = st.text_input("👤 User ID", help="A stable identifier for you, e.g. an email or username.")

    st.markdown("---")
    if _backend_healthy():
        st.success("Backend: connected")
    else:
        st.error(f"Backend unreachable at {API_URL}")

    st.markdown("---")
    st.info("Upload your resume → Ask questions → Get insights")

    if st.button("🗑️ Clear chat history"):
        st.session_state.chat = []
        st.rerun()

# ------------------ HEADER ------------------
st.title("💼 Resume RAG Career Assistant")
st.caption("Ask career questions grounded in your own resume — powered by AWS Bedrock + retrieval-augmented generation")

col1, col2 = st.columns([1, 2])

# ------------------ LEFT: UPLOAD ------------------
with col1:
    st.markdown("### 📄 Upload Resume")

    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx", "txt"])

    if st.button("📤 Upload Resume", type="primary", use_container_width=True):
        if not user_id:
            st.warning("⚠️ Enter a User ID first.")
        elif not uploaded_file:
            st.warning("⚠️ Choose a file to upload.")
        else:
            with st.spinner("Uploading and indexing your resume..."):
                try:
                    response = requests.post(
                        f"{API_URL}/api/v1/upload_resume",
                        data={"user_id": user_id},
                        files={"file": (uploaded_file.name, uploaded_file, uploaded_file.type)},
                        headers=_headers(),
                        timeout=REQUEST_TIMEOUT,
                    )
                except requests.RequestException as e:
                    st.error(f"❌ Could not reach the backend: {e}")
                    response = None

            if response is not None:
                if response.status_code == 200:
                    data = response.json()
                    st.success(f"✅ {data['message']} ({data['chunks_indexed']} chunks indexed)")
                    st.session_state.resume_uploaded = True
                else:
                    detail = response.json().get("detail", response.text)
                    st.error(f"❌ Upload failed: {detail}")

# ------------------ RIGHT: CHAT ------------------
with col2:
    st.markdown("### 💬 Ask Career Questions")

    with st.form("chat_form", clear_on_submit=True):
        question = st.text_input("Ask something about your career...")
        submitted = st.form_submit_button("Ask", type="primary")

        if submitted:
            if not user_id:
                st.warning("⚠️ Enter a User ID first.")
            elif not question:
                st.warning("⚠️ Enter a question.")
            else:
                with st.spinner("Thinking... 🤖"):
                    try:
                        response = requests.post(
                            f"{API_URL}/api/v1/ask_question",
                            json={"user_id": user_id, "question": question},
                            headers=_headers(),
                            timeout=REQUEST_TIMEOUT,
                        )
                    except requests.RequestException as e:
                        st.error(f"❌ Could not reach the backend: {e}")
                        response = None

                if response is not None:
                    if response.status_code == 200:
                        answer = response.json()["answer"]
                        st.session_state.chat.append(("user", question))
                        st.session_state.chat.append(("bot", answer))
                    else:
                        detail = response.json().get("detail", "Failed to get response")
                        st.error(f"❌ {detail}")

    for role, msg in st.session_state.chat:
        with st.chat_message("user" if role == "user" else "assistant"):
            st.markdown(msg)

# ------------------ FOOTER ------------------
st.markdown("---")
st.markdown("💡 **Try asking:**")
st.markdown(
    """
- What skills should I improve?
- Suggest job roles for me
- How can I improve my resume?
"""
)

