from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class EmbeddingMetadata:
    provider_name: str
    provider_version: str
    dimensions: int


class EmbeddingProvider(Protocol):
    @property
    def metadata(self) -> EmbeddingMetadata: ...

    def embed_many(self, texts: Sequence[str]) -> list[list[float]]: ...


class AnswerGenerationProvider(Protocol):
    """Phase 4 contract boundary; no implementation is provided in Phase 3."""

    def generate(self, question: str, evidence: Sequence[str]) -> str: ...
