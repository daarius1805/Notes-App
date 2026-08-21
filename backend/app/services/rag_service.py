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
            "answer": "I could not generate a full AI answer right now, but your note retrieval is working. Configure Gemini in backend/.env to enable complete answers.",
            "sources": [
                {"note_id": chunk.get("note_id", "unknown"), "title": chunk.get("note_title", "Unknown note"), "chunk_text": chunk.get("chunk_text", "")}
                for chunk in context_chunks
            ],
        }

    unique_chunks: list[str] = []
    seen_texts: set[str] = set()
    for chunk in context_chunks:
        chunk_text = (chunk.get("chunk_text") or "").strip()
        if not chunk_text:
            continue
        normalized = " ".join(chunk_text.split()).lower()
        if normalized in seen_texts:
            continue
        seen_texts.add(normalized)
        unique_chunks.append(chunk_text)

    context = "\n\n".join(unique_chunks)
    if not context:
        return {
            "answer": "I could not find any relevant note context for that question.",
            "sources": [],
        }

    cleaned_context = " ".join(context.split())
    short_context = cleaned_context[:700].rstrip()
    answer = f"From your notes: {short_context}"
    return {
        "answer": answer,
        "sources": [
            {"note_id": chunk.get("note_id", "unknown"), "title": chunk.get("note_title", "Unknown note"), "chunk_text": chunk.get("chunk_text", "")}
            for chunk in context_chunks
        ],
    }
