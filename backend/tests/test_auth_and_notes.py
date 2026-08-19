import os
import uuid

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_notes_rag.db")
os.environ.setdefault("JWT_SECRET", "test-secret")

from fastapi.testclient import TestClient

from app.main import app
from app.models.note_chunk import NoteChunk
from app.services.chunking_service import split_note_into_chunks
from app.services.retrieval_service import retrieve_relevant_chunks
from app.services.rag_service import answer_question


client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_login_and_notes_flow():
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"

    register = client.post(
        "/auth/register",
        json={"email": email, "password": "secret123"},
    )
    assert register.status_code == 201, register.text

    login = client.post(
        "/auth/login",
        json={"email": email, "password": "secret123"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    assert token

    notes = client.get("/notes", headers={"Authorization": f"Bearer {token}"})
    assert notes.status_code == 200

    create_note = client.post(
        "/notes",
        json={"title": "My first note", "content": "This is a test note."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_note.status_code == 201, create_note.text
    note_id = create_note.json()["id"]
    assert note_id

    unauth = client.get("/notes")
    assert unauth.status_code == 401


def test_split_note_into_chunks():
    text = " ".join([f"Sentence {index} about notes and retrieval and embeddings." for index in range(60)])
    chunks = split_note_into_chunks(text)

    assert len(chunks) >= 2
    assert all(chunk.strip() for chunk in chunks)
    assert all(len(chunk) > 0 for chunk in chunks)
    assert isinstance(chunks, list)


def test_note_chunk_model_exists():
    assert hasattr(NoteChunk, "note_id")
    assert hasattr(NoteChunk, "chunk_index")
    assert hasattr(NoteChunk, "chunk_text")


def test_retrieve_relevant_chunks_uses_similarity():
    question_vector = [1.0, 0.0]
    matching_vector = [1.0, 0.0]
    unrelated_vector = [0.0, 1.0]

    results = retrieve_relevant_chunks(
        question_vector=question_vector,
        chunks=[
            {"id": "a", "chunk_text": "alpha", "note_id": "n1", "note_title": "Note 1", "embedding": matching_vector},
            {"id": "b", "chunk_text": "beta", "note_id": "n2", "note_title": "Note 2", "embedding": unrelated_vector},
        ],
        limit=1,
    )

    assert results[0]["id"] == "a"
    assert results[0]["chunk_text"] == "alpha"


def test_answer_question_without_gemini_key_returns_structured_response():
    response = answer_question(question="What are my notes about?", context_chunks=[{"chunk_text": "Alpha note"}], api_key_missing=True)
    assert response["answer"]
    assert "not configured" in response["answer"].lower() or "gemini" in response["answer"].lower()
