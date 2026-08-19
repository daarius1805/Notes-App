import re

DEFAULT_CHUNK_SIZE = 900
DEFAULT_OVERLAP = 150


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def split_note_into_chunks(text: str, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_OVERLAP) -> list[str]:
    if not text:
        return []

    normalized = _normalize_text(text)
    if not normalized:
        return []

    if len(normalized) <= chunk_size:
        return [normalized]

    paragraphs = [part.strip() for part in re.split(r"\n\s*\n+", normalized) if part.strip()]
    if not paragraphs:
        paragraphs = [normalized]

    chunks: list[str] = []
    buffer = ""

    for paragraph in paragraphs:
        parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", paragraph) if part.strip()]
        if not parts:
            parts = [paragraph]

        for part in parts:
            candidate = f"{buffer} {part}".strip() if buffer else part
            if len(candidate) <= chunk_size:
                buffer = candidate
                continue

            if buffer:
                chunks.append(buffer.strip())

            if len(part) <= chunk_size:
                buffer = part
                continue

            start = 0
            while start < len(part):
                end = min(start + chunk_size, len(part))
                chunk = part[start:end].strip()
                if chunk:
                    chunks.append(chunk)
                if end >= len(part):
                    break
                start = max(end - overlap, start + 1)
            buffer = ""

    if buffer:
        chunks.append(buffer.strip())

    final_chunks = [chunk for chunk in chunks if chunk]
    if not final_chunks:
        return [normalized[:chunk_size]]

    if final_chunks[-1] == normalized:
        return final_chunks

    combined = []
    for chunk in final_chunks:
        if not combined or len(combined[-1]) + len(chunk) + 1 <= chunk_size:
            combined.append(chunk)
        else:
            combined.append(chunk)

    return [piece for piece in combined if piece]
