from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Bookmark:
    id: int
    url: str
    title: str
    description: str | None = None
