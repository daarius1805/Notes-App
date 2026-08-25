from __future__ import annotations

from typing import Any

from google import genai

from app.config import settings


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

    # De-duplicate chunks
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

    prompt = f"""You are a helpful assistant that answers questions based exclusively on the user's personal notes provided below.

Use only the information from the notes to answer. If the notes do not contain enough information to answer the question, say so clearly. Do not invent facts.

--- USER NOTES (context) ---
{context}
--- END OF NOTES ---

Question: {question}

Answer:"""

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    response = client.models.generate_content(
        model=settings.GEMINI_CHAT_MODEL,
        contents=prompt,
    )

    answer = (response.text or "").strip() or "No answer returned."

    return {
        "answer": answer,
        "sources": [
            {
                "note_id": chunk.get("note_id", "unknown"),
                "title": chunk.get("note_title", "Unknown note"),
                "chunk_text": chunk.get("chunk_text", ""),
            }
            for chunk in context_chunks
        ],
    }
