from datetime import datetime, timezone

from sqlmodel import Field, Relationship, SQLModel

if False:
    from app.models.note_chunk import NoteChunk
    from app.models.user import User


class Note(SQLModel, table=True):
    id: str = Field(default_factory=lambda: __import__("uuid").uuid4().hex, primary_key=True)
    user_id: str = Field(foreign_key="user.id", nullable=False, index=True)
    title: str = Field(nullable=False)
    content: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

    owner: "User" = Relationship(back_populates="notes")
    chunks: list["NoteChunk"] = Relationship(back_populates="note")
