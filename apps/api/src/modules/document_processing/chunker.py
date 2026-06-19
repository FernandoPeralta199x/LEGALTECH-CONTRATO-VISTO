from dataclasses import dataclass, field

from fastapi import HTTPException, status


DEFAULT_CHUNK_SIZE_CHARS = 1200
DEFAULT_CHUNK_OVERLAP_CHARS = 120
DEFAULT_MAX_TEXT_CHARS = 50_000


@dataclass(frozen=True)
class PlainTextChunk:
    chunk_index: int
    content: str
    page_number: int | None = None
    metadata: dict = field(default_factory=lambda: {"source": "local_text"})


def chunk_plain_text(
    text: str,
    *,
    chunk_size_chars: int = DEFAULT_CHUNK_SIZE_CHARS,
    chunk_overlap_chars: int = DEFAULT_CHUNK_OVERLAP_CHARS,
    max_text_chars: int = DEFAULT_MAX_TEXT_CHARS,
) -> list[PlainTextChunk]:
    normalized_text = text.strip()
    if not normalized_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text for local processing must not be empty.",
        )

    if len(normalized_text) > max_text_chars:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Text for local processing exceeds the configured maximum size.",
        )

    if chunk_size_chars <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="chunk_size_chars must be greater than zero.",
        )

    if chunk_overlap_chars < 0 or chunk_overlap_chars >= chunk_size_chars:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="chunk_overlap_chars must be lower than chunk_size_chars.",
        )

    chunks: list[PlainTextChunk] = []
    start = 0
    step = chunk_size_chars - chunk_overlap_chars

    while start < len(normalized_text):
        end = min(start + chunk_size_chars, len(normalized_text))
        content = normalized_text[start:end].strip()
        if content:
            chunks.append(
                PlainTextChunk(
                    chunk_index=len(chunks),
                    content=content,
                )
            )
        start += step

    return chunks
