import hashlib
import math
from collections.abc import Sequence

from app.providers.base import EmbeddingMetadata

PROVIDER_NAME = "deterministic-local"
PROVIDER_VERSION = "hash-char-ngram-v1"
DIMENSIONS = 32


class DeterministicEmbeddingProvider:
    @property
    def metadata(self) -> EmbeddingMetadata:
        return EmbeddingMetadata(PROVIDER_NAME, PROVIDER_VERSION, DIMENSIONS)

    def embed_many(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * DIMENSIONS
        ngrams = list(text) + [text[index : index + 2] for index in range(len(text) - 1)]
        for ngram in ngrams:
            digest = hashlib.sha256(f"{PROVIDER_VERSION}\0{ngram}".encode()).digest()
            bucket = int.from_bytes(digest[:4], "big") % DIMENSIONS
            vector[bucket] += 1.0 if digest[4] & 1 else -1.0
        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude == 0:
            return vector
        return [value / magnitude for value in vector]
