from pydantic import BaseModel, ConfigDict


class ChatQuery(BaseModel):
    question: str


class SourceReference(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    note_id: str
    title: str
    chunk_text: str


class ChatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    answer: str
    sources: list[SourceReference] = []
