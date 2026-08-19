import json

from google import genai

from app.config import settings


def get_embedding_client() -> genai.Client | None:
    if not settings.GEMINI_API_KEY:
        return None
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def embed_texts(texts: list[str]) -> list[list[float] | None]:
    if not texts:
        return []

    client = get_embedding_client()
    if client is None:
        return [None for _ in texts]

    response = client.models.embed_content(
        model=settings.GEMINI_EMBEDDING_MODEL,
        contents=texts,
    )

    embeddings = response.embeddings or []
    result: list[list[float] | None] = []
    for embedding in embeddings:
        values = getattr(embedding, "values", None)
        if values is None:
            result.append(None)
            continue
        result.append([float(value) for value in values])

    if len(result) < len(texts):
        result.extend([None] * (len(texts) - len(result)))

    return result


def embed_texts_as_json(texts: list[str]) -> list[str | None]:
    vectors = embed_texts(texts)
    return [json.dumps(vector) if vector else None for vector in vectors]
