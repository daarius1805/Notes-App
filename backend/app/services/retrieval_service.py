import math
from typing import Any


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        return 0.0

    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def retrieve_relevant_chunks(
    question_vector: list[float],
    chunks: list[dict[str, Any]],
    limit: int = 3,
) -> list[dict[str, Any]]:
    scored: list[tuple[float, dict[str, Any]]] = []

    for chunk in chunks:
        embedding = chunk.get("embedding")
        if not embedding:
            continue
        similarity = cosine_similarity(question_vector, embedding)
        scored.append((similarity, chunk))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [chunk for _, chunk in scored[:limit]]
