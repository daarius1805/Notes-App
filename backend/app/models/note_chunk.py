from datetime import datetime, timezone

from sqlmodel import Field, Relationship, SQLModel

if False:
    from app.models.note import Note


class NoteChunk(SQLModel, table=True):
    __tablename__ = "note_chunk"

    id: str = Field(default_factory=lambda: __import__("uuid").uuid4().hex, primary_key=True)
    note_id: str = Field(foreign_key="note.id", nullable=False, index=True)
    chunk_index: int = Field(default=0, nullable=False, index=True)
    chunk_text: str = Field(nullable=False)
    embedding: str | None = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

    note: "Note" = Relationship(back_populates="chunks")
