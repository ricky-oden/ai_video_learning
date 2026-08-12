from pathlib import Path


def test_phase3_pipeline_has_no_external_provider_or_network_configuration() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    checked_paths = [
        backend_root / "app" / "application",
        backend_root / "app" / "providers",
        backend_root / "fixtures" / "transcripts",
    ]
    contents = "\n".join(
        path.read_text(encoding="utf-8")
        for root in checked_paths
        for path in root.rglob("*")
        if path.is_file() and path.suffix in {".py", ".json"}
    ).lower()
    requirements = (backend_root / "requirements.txt").read_text(encoding="utf-8").lower()

    assert "http://" not in contents
    assert "https://" not in contents
    assert "openai" not in contents + requirements
    assert "api_key" not in contents
    assert "requests." not in contents
    assert "httpx." not in contents
