from __future__ import annotations

import os
import subprocess
import sys
import time
from importlib import import_module
from inspect import cleandoc
from pathlib import Path
from typing import Iterable, Mapping, Optional, Tuple, Union

from .install import install_editor_cli, install_system_tools, setup_python_environment
from .mapper_config import ExtraMappers, remove_path, setup_editor_mappers


DEFAULT_RUNTIME_DIR = "/content/drive/MyDrive/Colab Notebooks/runtime"
SUPPORTED_EDITORS = ("vscode", "cursor")


def get_editor_message(editor: str) -> str:
    editor_names = {"cursor": "Cursor", "vscode": "VSCode"}
    editor_name = editor_names.get(editor, editor)
    return cleandoc(
        f"""
    - Ready!
    - Open {editor_name} on your laptop and open the command prompt
    - Select: 'Remote-Tunnels: Connect to Tunnel' to connect to colab
    """
    ).strip()


def _run_and_capture(
    command: Iterable[str], *, env: Optional[Mapping[str, str]] = None
) -> subprocess.CompletedProcess:
    return subprocess.run(
        list(command),
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=dict(env) if env else None,
    )


def _detect_provider(auth_output: str) -> Optional[str]:
    normalized = auth_output.lower()
    if "github" in normalized:
        return "github"
    if "microsoft" in normalized:
        return "microsoft"
    return None


def _check_tunnel_auth(
    cli_binary: Path, *, env: Optional[Mapping[str, str]] = None
) -> Tuple[bool, Optional[str], str]:
    command = [str(cli_binary), "tunnel", "user", "show"]
    result = _run_and_capture(command, env=env)
    output = (result.stdout or "").strip()
    lowered = output.lower()

    if result.returncode != 0:
        return False, None, output

    if any(item in lowered for item in ("not logged in", "logged out", "no account")):
        return False, None, output

    if "logged in" in lowered or "signed in" in lowered or output:
        return True, _detect_provider(output), output

    return False, None, output


def login_tunnel(
    cli_binary: Path,
    provider: str,
    *,
    env: Optional[Mapping[str, str]] = None,
) -> None:
    command = [str(cli_binary), "tunnel", "user", "login", "--provider", provider]
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=dict(env) if env else None,
    )

    if process.stdout is None:
        raise RuntimeError("Failed to stream tunnel login output")

    while True:
        line = process.stdout.readline()
        if line == "" and process.poll() is not None:
            break
        if line:
            print(line.strip())

    if process.returncode:
        raise RuntimeError(f"Tunnel login failed with exit code {process.returncode}")


def ensure_tunnel_auth(
    cli_binary: Path,
    provider: str,
    *,
    env: Optional[Mapping[str, str]] = None,
) -> None:
    is_valid, existing_provider, output = _check_tunnel_auth(cli_binary, env=env)

    if is_valid and (existing_provider is None or existing_provider == provider):
        print("Tunnel authentication already exists and is valid. Skipping login.")
        return

    if is_valid and existing_provider and existing_provider != provider:
        print(
            f"Tunnel auth exists for '{existing_provider}', "
            f"re-authenticating with '{provider}'."
        )
    else:
        if output:
            print(output)
        print("No valid tunnel authentication detected. Starting login flow...")

    login_tunnel(cli_binary, provider, env=env)


def start_tunnel(
    editor: str,
    cli_binary: Path,
    *,
    env: Optional[Mapping[str, str]] = None,
) -> None:
    command = [
        str(cli_binary),
        "tunnel",
        "--accept-server-license-terms",
        "--name",
        "colab-connect",
    ]

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=dict(env) if env else None,
    )

    if process.stdout is None:
        raise RuntimeError("Failed to stream tunnel output")

    show_outputs = False
    while True:
        line = process.stdout.readline()
        if line == "" and process.poll() is not None:
            break
        if not line:
            continue

        stripped = line.strip()
        lowered = stripped.lower()
        if show_outputs:
            print(stripped)
        if "to grant access to the server" in lowered:
            print(stripped)
        if "open this link" in lowered:
            print("Starting the tunnel")
            time.sleep(5)
            print(get_editor_message(editor))
            print("Logs:")
            show_outputs = True

    if process.returncode:
        raise RuntimeError(f"Tunnel failed with exit code {process.returncode}")


def is_colab() -> bool:
    return "google.colab" in sys.modules


def _mount_drive() -> None:
    drive = import_module("google.colab.drive")
    drive.mount("/content/drive")


def _ensure_colab_shortcut(runtime_path: Path) -> None:
    shortcut_path = Path("/colab")
    remove_path(shortcut_path)
    shortcut_path.symlink_to(runtime_path, target_is_directory=True)


def _build_tunnel_env() -> Mapping[str, str]:
    env = os.environ.copy()
    env["VSCODE_CLI_USE_FILE_KEYCHAIN"] = "1"
    env["VSCODE_CLI_DISABLE_KEYCHAIN_ENCRYPT"] = "1"
    return env


def colabconnect(
    editor: str = "vscode",
    provider: str = "github",
    runtime_dir: Union[str, Path] = DEFAULT_RUNTIME_DIR,
    use_mapper: Optional[Iterable[str]] = None,
    extra_mappers: ExtraMappers = None,
    use_uv: bool = False,
    create_venv: bool = False,
) -> None:
    editor = editor.lower().strip()
    provider = provider.lower().strip()

    if editor not in SUPPORTED_EDITORS:
        raise ValueError("editor must be either 'vscode' or 'cursor'")

    if is_colab():
        print("Mounting Google Drive...")
        _mount_drive()

    runtime_path = Path(runtime_dir).expanduser()
    runtime_path.mkdir(parents=True, exist_ok=True)

    if is_colab():
        _ensure_colab_shortcut(runtime_path)

    print("Setting up persistent mapper folders...")
    setup_editor_mappers(
        runtime_path,
        default_mapper=editor,
        use_mapper=use_mapper,
        extra_mappers=extra_mappers,
    )

    if use_uv and create_venv:
        print("Installing python tools with uv in a runtime virtualenv...")
    elif use_uv:
        print("Installing python tools with uv in the current environment...")
    elif create_venv:
        print("Creating runtime virtualenv and installing python tools with pip...")
    else:
        print("Installing python tools with pip (default, no virtualenv)...")

    setup_python_environment(
        runtime_path,
        use_uv=use_uv,
        create_venv=create_venv,
    )
    install_system_tools()

    print(f"Installing {editor} CLI...")
    cli_binary = install_editor_cli(editor, runtime_path)

    tunnel_env = _build_tunnel_env()
    print("Checking tunnel authentication...")
    ensure_tunnel_auth(cli_binary, provider, env=tunnel_env)

    print("Starting tunnel...")
    start_tunnel(editor, cli_binary, env=tunnel_env)
