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


@dataclass(frozen=True)
class EvidenceInput:
    citation_id: str
    text: str


@dataclass(frozen=True)
class GeneratedAnswer:
    body: str
    citation_ids: tuple[str, ...]
    provider_name: str
    provider_version: str


class AnswerGenerationProvider(Protocol):
    def generate(self, question: str, evidence: Sequence[EvidenceInput]) -> GeneratedAnswer: ...
