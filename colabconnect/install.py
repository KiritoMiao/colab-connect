from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Mapping, Optional, Sequence, Tuple


UV_INSTALL_SCRIPT = "https://astral.sh/uv/install.sh"
PYTHON_TOOLS = (
    "flake8",
    "black",
    "ipywidgets",
    "twine",
    "ipykernel",
)

EDITOR_DOWNLOADS = {
    "vscode": {
        "url": "https://code.visualstudio.com/sha/download?build=stable&os=cli-alpine-x64",
        "binary": "code",
    },
    "cursor": {
        "url": "https://api2.cursor.sh/updates/download-latest?os=cli-alpine-x64",
        "binary": "cursor",
    },
}


def _run(
    command: Sequence[str],
    *,
    cwd: Optional[Path] = None,
    env: Optional[Mapping[str, str]] = None,
    capture_output: bool = False,
) -> subprocess.CompletedProcess:
    completed = subprocess.run(
        list(command),
        cwd=str(cwd) if cwd else None,
        env=dict(env) if env else None,
        check=False,
        text=True,
        stdout=subprocess.PIPE if capture_output else None,
        stderr=subprocess.STDOUT if capture_output else None,
    )

    if completed.returncode != 0:
        output = (completed.stdout or "").strip()
        message = f"Command failed ({completed.returncode}): {' '.join(command)}"
        if output:
            message = f"{message}\n{output}"
        raise RuntimeError(message)

    return completed


def install_uv() -> Path:
    existing = shutil.which("uv")
    if existing:
        return Path(existing)

    installer_path = Path("/tmp/uv-installer.sh")
    _run(["curl", "-LsSf", UV_INSTALL_SCRIPT, "-o", str(installer_path)])
    _run(["sh", str(installer_path)])

    candidates = (
        Path.home() / ".local" / "bin" / "uv",
        Path.home() / ".cargo" / "bin" / "uv",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate

    discovered = shutil.which("uv")
    if discovered:
        return Path(discovered)

    raise RuntimeError("uv installation completed but uv binary was not found")


def create_runtime_venv(uv_bin: Path, runtime_dir: Path) -> Path:
    venv_dir = runtime_dir / ".venv"
    _run([str(uv_bin), "venv", str(venv_dir)])

    python_bin = venv_dir / "bin" / "python"
    if not python_bin.exists():
        raise RuntimeError(f"Could not find virtualenv python at: {python_bin}")

    return python_bin


def install_python_tools(uv_bin: Path, python_bin: Path) -> None:
    _run(
        [
            str(uv_bin),
            "pip",
            "install",
            "--python",
            str(python_bin),
            "--upgrade",
            *PYTHON_TOOLS,
        ]
    )


def install_system_tools() -> None:
    _run(["apt", "install", "-y", "htop"])


def _discover_editor_binary(cli_dir: Path, binary_name: str) -> Path:
    direct = cli_dir / binary_name
    if direct.exists():
        return direct

    matches = [path for path in cli_dir.rglob(binary_name) if path.is_file()]
    if len(matches) == 1:
        return matches[0]

    raise RuntimeError(f"Unable to find '{binary_name}' binary in: {cli_dir}")


def install_editor_cli(editor: str, runtime_dir: Path) -> Path:
    if editor not in EDITOR_DOWNLOADS:
        raise ValueError(f"Unsupported editor: {editor}")

    cli_dir = runtime_dir / "editor-cli" / editor
    cli_dir.mkdir(parents=True, exist_ok=True)

    download_info = EDITOR_DOWNLOADS[editor]
    archive_path = cli_dir / f"{editor}_cli.tar.gz"

    _run(
        [
            "curl",
            "-Lk",
            download_info["url"],
            "--output",
            str(archive_path),
        ]
    )
    _run(["tar", "-xf", str(archive_path), "-C", str(cli_dir)])

    binary_path = _discover_editor_binary(cli_dir, download_info["binary"])
    binary_path.chmod(binary_path.stat().st_mode | 0o111)
    return binary_path


def setup_python_environment(runtime_dir: Path) -> Tuple[Path, Path]:
    uv_bin = install_uv()
    python_bin = create_runtime_venv(uv_bin, runtime_dir)
    install_python_tools(uv_bin, python_bin)
    return uv_bin, python_bin
