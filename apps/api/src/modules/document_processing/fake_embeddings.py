import hashlib


FAKE_EMBEDDING_DIMENSIONS = 1536


def fake_embedding_for_text(
    text: str,
    *,
    dimensions: int = FAKE_EMBEDDING_DIMENSIONS,
) -> list[float]:
    seed = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    counter = 0

    while len(values) < dimensions:
        block = hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
        for index in range(0, len(block), 4):
            integer = int.from_bytes(block[index : index + 4], "big")
            values.append((integer / 2**31) - 1.0)
            if len(values) == dimensions:
                break
        counter += 1

    return values
