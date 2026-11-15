"""Non-overwriting, credential-checked evaluation evidence files."""

import json
import os
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_EVIDENCE_ROOT = Path("artifacts") / "reminder-agent"
PROVIDER_KEY_PATTERN = re.compile(r"sk-[A-Za-z0-9_-]{20,}")


def create_run_directory(root: Path | None = None) -> Path:
    """Create a unique run directory without replacing earlier evidence."""
    evidence_root = root or DEFAULT_EVIDENCE_ROOT
    evidence_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    while True:
        run_dir = evidence_root / f"{timestamp}-{secrets.token_hex(4)}"
        try:
            run_dir.mkdir()
        except FileExistsError:
            continue
        return run_dir


def assert_credential_free(serialized: str) -> None:
    if PROVIDER_KEY_PATTERN.search(serialized):
        raise ValueError("evidence cannot contain provider credentials")
    api_key = os.environ.get("GROQ_API_KEY", "")
    if api_key and api_key in serialized:
        raise ValueError("evidence cannot contain provider credentials")


def write_json_evidence(run_dir: Path, filename: str, data: Any) -> Path:
    """Write one JSON file exclusively after checking it for provider credentials."""
    if (
        not filename
        or Path(filename).name != filename
        or "/" in filename
        or "\\" in filename
        or filename in {".", ".."}
    ):
        raise ValueError("evidence filename must be a simple file name")
    destination = run_dir / filename
    if destination.parent.resolve() != run_dir.resolve():
        raise ValueError("evidence path must stay inside the run directory")

    serialized = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    assert_credential_free(serialized)
    with destination.open("x", encoding="utf-8", newline="\n") as evidence_file:
        evidence_file.write(serialized)
    return destination
