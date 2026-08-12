from collections.abc import Sequence

from app.providers.base import EvidenceInput, GeneratedAnswer

PROVIDER_NAME = "deterministic-local"
PROVIDER_VERSION = "grounded-extractive-v1"


class GroundedExtractiveAnswerProvider:
    def generate(self, question: str, evidence: Sequence[EvidenceInput]) -> GeneratedAnswer:
        del question
        return GeneratedAnswer(
            body="\n".join(item.text for item in evidence),
            citation_ids=tuple(item.citation_id for item in evidence),
            provider_name=PROVIDER_NAME,
            provider_version=PROVIDER_VERSION,
        )
