from uuid import UUID


def parse_uuid(value: UUID | str) -> UUID:
    if isinstance(value, UUID):
        return value

    return UUID(str(value))

