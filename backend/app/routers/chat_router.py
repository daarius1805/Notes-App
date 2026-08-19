from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.dependencies import get_current_user
from app.models.note import Note
from app.models.note_chunk import NoteChunk
from app.models.user import User
from app.schemas.chat_schema import ChatQuery, ChatResponse
from app.services.embedding_service import get_embedding_client
from app.services.rag_service import answer_question
from app.services.retrieval_service import retrieve_relevant_chunks

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat_with_notes(
    payload: ChatQuery,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if not payload.question.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question cannot be empty")

    note_chunks = session.exec(
        select(NoteChunk, Note.title)
        .join(Note, Note.id == NoteChunk.note_id)
        .where(Note.user_id == current_user.id)
    ).all()

    chunk_data: list[dict] = []
    for note_chunk, note_title in note_chunks:
        embedding_text = note_chunk.embedding
        if not embedding_text:
            continue
        try:
            import ast
            vector = ast.literal_eval(embedding_text)
        except Exception:
            continue

        chunk_data.append({
            "id": note_chunk.id,
            "note_id": note_chunk.note_id,
            "note_title": note_title,
            "chunk_text": note_chunk.chunk_text,
            "embedding": vector,
        })

    if not chunk_data:
        return answer_question(question=payload.question, context_chunks=[], api_key_missing=True)

    try:
        from app.services.embedding_service import embed_texts
        question_vector = embed_texts([payload.question])[0]
    except Exception:
        question_vector = None

    if not question_vector:
        question_vector = [0.0 for _ in range(3)]

    relevant = retrieve_relevant_chunks(question_vector, chunk_data, limit=3)
    return answer_question(question=payload.question, context_chunks=relevant, api_key_missing=get_embedding_client() is None)
