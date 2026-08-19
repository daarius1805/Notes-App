from datetime import datetime, timezone

from sqlmodel import Field, Relationship, SQLModel

if False:
    from app.models.note import Note


class User(SQLModel, table=True):
    __tablename__ = "user"

    id: str = Field(default_factory=lambda: __import__("uuid").uuid4().hex, primary_key=True)
    email: str = Field(index=True, unique=True, nullable=False)
    password_hash: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

    notes: list["Note"] = Relationship(back_populates="owner")
