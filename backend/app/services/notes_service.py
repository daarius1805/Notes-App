from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlmodel import Session, delete, select

from app.models.note import Note
from app.models.note_chunk import NoteChunk
from app.services.chunking_service import split_note_into_chunks
from app.services.embedding_service import embed_texts


def list_user_notes(session: Session, user_id: str) -> list[Note]:
    return session.exec(select(Note).where(Note.user_id == user_id)).all()


def create_note(session: Session, user_id: str, title: str, content: str) -> Note:
    note = Note(user_id=user_id, title=title, content=content)
    note.created_at = datetime.now(timezone.utc)
    note.updated_at = datetime.now(timezone.utc)
    session.add(note)
    session.commit()
    session.refresh(note)

    chunks = split_note_into_chunks(content)
    if chunks:
        vectors = embed_texts(chunks)
        for index, chunk_text in enumerate(chunks):
            vector = vectors[index] if index < len(vectors) else None
            session.add(
                NoteChunk(
                    note_id=note.id,
                    chunk_index=index,
                    chunk_text=chunk_text,
                    embedding=str(vector) if vector else None,
                )
            )
    session.commit()
    session.refresh(note)
    return note


def get_note_for_user(session: Session, note_id: str, user_id: str) -> Note:
    note = session.get(Note, note_id)
    if note is None or note.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return note


def update_note(session: Session, note_id: str, user_id: str, title: str | None, content: str | None) -> Note:
    note = get_note_for_user(session, note_id, user_id)
    if title is not None:
        note.title = title
    if content is not None:
        note.content = content
    note.updated_at = datetime.now(timezone.utc)
    session.add(note)
    session.commit()
    session.refresh(note)
    return note


def delete_note(session: Session, note_id: str, user_id: str) -> None:
    note = get_note_for_user(session, note_id, user_id)

    # Remove chunk rows first to avoid FK nulling on environments without delete cascade.
    session.exec(delete(NoteChunk).where(NoteChunk.note_id == note.id))
    session.delete(note)
    session.commit()
