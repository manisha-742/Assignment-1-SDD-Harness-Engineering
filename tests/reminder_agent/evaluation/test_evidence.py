import pytest

from reminder_agent.evidence import create_run_directory, write_json_evidence


def test_run_directories_are_unique_and_non_overwriting(tmp_path) -> None:
    first = create_run_directory(tmp_path)
    second = create_run_directory(tmp_path)

    assert first != second
    assert first.is_dir() and second.is_dir()


def test_evidence_writer_never_overwrites_a_file(tmp_path) -> None:
    run_dir = create_run_directory(tmp_path)
    destination = write_json_evidence(run_dir, "manifest.json", {"status": "initial"})

    with pytest.raises(FileExistsError):
        write_json_evidence(run_dir, "manifest.json", {"status": "replaced"})

    assert destination.read_text(encoding="utf-8").find("initial") >= 0


def test_evidence_writer_rejects_credentials_in_artifact_data(
    tmp_path, monkeypatch
) -> None:
    secret = "synthetic-evidence-secret"
    monkeypatch.setenv("GROQ_API_KEY", secret)
    run_dir = create_run_directory(tmp_path)

    with pytest.raises(ValueError, match="credential"):
        write_json_evidence(run_dir, "output.json", {"captured": secret})


def test_evidence_writer_rejects_real_looking_provider_keys(tmp_path) -> None:
    run_dir = create_run_directory(tmp_path)

    with pytest.raises(ValueError, match="credential"):
        write_json_evidence(run_dir, "output.json", {"captured": "sk-" + "A" * 24})


def test_evidence_filename_cannot_escape_run_directory(tmp_path) -> None:
    run_dir = create_run_directory(tmp_path)

    with pytest.raises(ValueError):
        write_json_evidence(run_dir, "..\\escaped.json", {"ok": True})
