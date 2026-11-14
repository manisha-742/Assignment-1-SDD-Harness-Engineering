import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest


@dataclass(frozen=True)
class CliResult:
    returncode: int
    stdout: str
    stderr: str


@pytest.fixture
def run_cli(tmp_path: Path):
    source_path = Path(__file__).resolve().parents[1] / "src"

    def run(*arguments: str) -> CliResult:
        environment = os.environ.copy()
        existing_pythonpath = environment.get("PYTHONPATH")
        environment["PYTHONPATH"] = os.pathsep.join(
            part for part in (str(source_path), existing_pythonpath) if part
        )
        result = subprocess.run(
            [sys.executable, "-m", "smart_todo", *arguments],
            cwd=tmp_path,
            env=environment,
            capture_output=True,
            check=False,
            text=True,
        )
        return CliResult(result.returncode, result.stdout, result.stderr)

    return run
