import json
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path


def _commit_id(repo_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            check=False,
            text=True,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    commit_id = result.stdout.strip()
    return commit_id or None


def _tool_version(distribution: str) -> str:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return "unavailable"


def _run_command(name: str, command: list[str], cwd: Path) -> dict[str, object]:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            check=False,
            text=True,
        )
    except OSError as error:
        return {
            "name": name,
            "command": command,
            "returncode": None,
            "stdout": "",
            "stderr": str(error),
        }
    return {
        "name": name,
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def run_harness(repo_root: str | Path | None = None) -> Path:
    root = (
        Path(repo_root)
        if repo_root is not None
        else Path(__file__).resolve().parents[1]
    )
    root = root.resolve()
    evidence_root = root / "artifacts" / "harness"
    evidence_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_directory = Path(
        tempfile.mkdtemp(prefix=f"run-{timestamp}-", dir=evidence_root)
    )
    started_at = datetime.now(timezone.utc)
    commit_id = _commit_id(root)

    commands = [
        (
            "pytest",
            [
                sys.executable,
                "-m",
                "pytest",
                f"--junitxml={run_directory / 'pytest.xml'}",
            ],
        ),
        ("ruff check", ["ruff", "check", "."]),
        ("ruff format", ["ruff", "format", "--check", "."]),
        ("bandit", ["bandit", "-q", "-r", "src"]),
    ]
    results = [_run_command(name, command, root) for name, command in commands]
    status = "PASS" if all(result["returncode"] == 0 for result in results) else "FAIL"
    evidence = {
        "run_id": run_directory.name,
        "started_at_utc": started_at.isoformat(),
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "commit_id": commit_id,
        "python_version": platform.python_version(),
        "tool_versions": {
            "pytest": _tool_version("pytest"),
            "ruff": _tool_version("ruff"),
            "bandit": _tool_version("bandit"),
        },
        "commands": results,
        "aggregate_status": status,
    }
    (run_directory / "run.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return run_directory


def main() -> int:
    run_directory = run_harness()
    evidence = json.loads((run_directory / "run.json").read_text(encoding="utf-8"))
    print(f"{evidence['aggregate_status']} {run_directory}")
    return 0 if evidence["aggregate_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
