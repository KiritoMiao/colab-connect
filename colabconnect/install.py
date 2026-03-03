from __future__ import annotations

import shutil
import subprocess
import sys
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


def create_runtime_venv(runtime_dir: Path, *, uv_bin: Optional[Path] = None) -> Path:
    venv_dir = runtime_dir / ".venv"
    if uv_bin:
        _run([str(uv_bin), "venv", str(venv_dir)])
    else:
        _run([sys.executable, "-m", "venv", str(venv_dir)])

    python_bin = venv_dir / "bin" / "python"
    if not python_bin.exists():
        raise RuntimeError(f"Could not find virtualenv python at: {python_bin}")

    return python_bin


def install_python_tools_with_uv(
    uv_bin: Path,
    *,
    python_bin: Optional[Path] = None,
) -> None:
    command = [str(uv_bin), "pip", "install"]
    if python_bin:
        command.extend(["--python", str(python_bin)])
    else:
        command.append("--system")

    command.extend(["--upgrade", *PYTHON_TOOLS])
    _run(command)


def install_python_tools_with_pip(*, python_bin: Optional[Path] = None) -> None:
    command = [
        str(python_bin or Path(sys.executable)),
        "-m",
        "pip",
        "install",
        "--upgrade",
    ]
    command.extend(PYTHON_TOOLS)
    _run(command)


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


def setup_python_environment(
    runtime_dir: Path,
    *,
    use_uv: bool = False,
    create_venv: bool = False,
) -> Tuple[Optional[Path], Optional[Path]]:
    uv_bin: Optional[Path] = install_uv() if use_uv else None
    python_bin: Optional[Path] = None

    if create_venv:
        python_bin = create_runtime_venv(runtime_dir, uv_bin=uv_bin)

    if use_uv:
        if uv_bin is None:
            raise RuntimeError("uv requested but uv binary was not found")
        install_python_tools_with_uv(uv_bin=uv_bin, python_bin=python_bin)
    else:
        install_python_tools_with_pip(python_bin=python_bin)

    return uv_bin, python_bin
