from app.application.transcripts import (
    CHUNKING_VERSION,
    FIXTURE_REGISTRY,
    NORMALIZATION_VERSION,
    FixtureSegment,
    TranscriptFixture,
    TranscriptImportError,
    build_chunks,
    normalize_text,
    validate_and_normalize,
)


def fixture(*segments: FixtureSegment) -> TranscriptFixture:
    return TranscriptFixture(fixture_id="test", segments=list(segments))


def segment(sequence: int, start: int, end: int, text: str) -> FixtureSegment:
    return FixtureSegment(sequence=sequence, start_ms=start, end_ms=end, text=text)


def test_normalization_is_nfkc_and_whitespace_only() -> None:
    assert NORMALIZATION_VERSION == "nfkc-whitespace-v1"
    assert normalize_text("  ＡＢＣ\n\t  カット  ") == "ABC カット"


def test_validation_rejects_sequence_time_overlap_and_blank_text() -> None:
    invalid_cases = (
        fixture(segment(2, 0, 10, "text")),
        fixture(segment(1, -1, 10, "text")),
        fixture(segment(1, 10, 10, "text")),
        fixture(segment(1, 0, 10, "one"), segment(2, 9, 20, "two")),
        fixture(segment(1, 0, 10, " \n\t ")),
    )
    for invalid in invalid_cases:
        try:
            validate_and_normalize(invalid)
        except TranscriptImportError as exception:
            assert exception.code == "INVALID_TRANSCRIPT"
        else:
            raise AssertionError("invalid transcript was accepted")


def test_original_text_and_deterministic_chunk_overlap_are_preserved() -> None:
    source = fixture(
        segment(1, 0, 10, " Ａ "),
        segment(2, 10, 20, "B"),
        segment(3, 20, 30, "C"),
        segment(4, 30, 40, "D"),
        segment(5, 40, 50, "E"),
    )
    normalized = validate_and_normalize(source)
    first = build_chunks(normalized)
    second = build_chunks(normalized)

    assert CHUNKING_VERSION == "segment-window-3-overlap-1-v1"
    assert normalized[0].original_text == " Ａ "
    assert normalized[0].normalized_text == "A"
    assert first == second
    assert [(item.first_segment_sequence, item.last_segment_sequence) for item in first] == [
        (1, 3),
        (3, 5),
    ]
    assert [(item.start_ms, item.end_ms) for item in first] == [(0, 30), (20, 50)]


def test_fixture_registry_uses_only_local_json_files() -> None:
    assert FIXTURE_REGISTRY
    for fixture_id, (_, path) in FIXTURE_REGISTRY.items():
        assert "://" not in fixture_id
        assert path.suffix == ".json"
        assert path.is_file()
