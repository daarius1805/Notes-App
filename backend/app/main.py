from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_db_and_tables
from app.models.note_chunk import NoteChunk
from app.routers.auth_router import router as auth_router
from app.routers.chat_router import router as chat_router
from app.routers.notes_router import router as notes_router

app = FastAPI(title="Notes RAG API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(notes_router)
app.include_router(chat_router)

create_db_and_tables()


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Notes RAG API is running"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
