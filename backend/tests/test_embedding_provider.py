import json
import math
import subprocess
import sys

from app.providers.deterministic_embedding import DeterministicEmbeddingProvider


def test_embedding_metadata_dimensions_finite_and_order() -> None:
    provider = DeterministicEmbeddingProvider()
    vectors = provider.embed_many(["first", "second", "first"])

    assert provider.metadata.provider_name == "deterministic-local"
    assert provider.metadata.provider_version == "hash-char-ngram-v1"
    assert provider.metadata.dimensions == 32
    assert all(len(vector) == 32 for vector in vectors)
    assert all(math.isfinite(value) for vector in vectors for value in vector)
    assert vectors[0] == vectors[2]
    assert vectors[0] != vectors[1]


def test_embedding_is_identical_in_another_process() -> None:
    expected = DeterministicEmbeddingProvider().embed_many(["同じ 入力"])[0]
    code = (
        "import json; "
        "from app.providers.deterministic_embedding import DeterministicEmbeddingProvider; "
        "print(json.dumps(DeterministicEmbeddingProvider().embed_many(['同じ 入力'])[0]))"
    )
    actual = json.loads(subprocess.check_output([sys.executable, "-c", code], text=True))
    assert actual == expected
