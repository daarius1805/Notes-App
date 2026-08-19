from __future__ import annotations

from typing import Any


def answer_question(
    *,
    question: str,
    context_chunks: list[dict[str, Any]],
    api_key_missing: bool = False,
) -> dict[str, Any]:
    if api_key_missing:
        return {
            "answer": "Gemini is not configured yet. Add your API key to backend/.env to enable note-based answers.",
            "sources": [
                {"note_id": chunk.get("note_id", "unknown"), "title": chunk.get("note_title", "Unknown note"), "chunk_text": chunk.get("chunk_text", "")}
                for chunk in context_chunks
            ],
        }

    context = "\n\n".join(chunk.get("chunk_text", "") for chunk in context_chunks if chunk.get("chunk_text"))
    if not context:
        return {
            "answer": "I could not find any relevant note context for that question.",
            "sources": [],
        }

    answer = (
        f"Based on your notes, here is the answer to: {question}\n\n"
        f"Context:\n{context}"
    )
    return {
        "answer": answer,
        "sources": [
            {"note_id": chunk.get("note_id", "unknown"), "title": chunk.get("note_title", "Unknown note"), "chunk_text": chunk.get("chunk_text", "")}
            for chunk in context_chunks
        ],
    }
