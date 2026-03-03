from __future__ import annotations

import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Tuple, Union


MapperEntry = Tuple[str, Path]
MapperMap = Mapping[str, Union[str, Path]]
MapperPairs = Iterable[Tuple[str, Union[str, Path]]]
ExtraMappers = Optional[Union[MapperMap, MapperPairs, Tuple[str, Union[str, Path]]]]


PRESET_MAPPERS = {
    "vscode": (
        ("vscode-config", "~/.config/Code"),
        ("vscode-dot", "~/.vscode"),
        ("vscode-server", "~/.vscode-server"),
        ("vscode-cli", "~/.vscode-cli"),
    ),
    "cursor": (
        ("cursor-config", "~/.config/Cursor"),
        ("cursor-dot", "~/.cursor"),
    ),
    "opencode": (
        ("opencode-config", "~/.config/OpenCode"),
        ("opencode-dot", "~/.opencode"),
    ),
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
        return
    if path.is_dir():
        shutil.rmtree(path)


def force_symlink(target: Path, link_path: Path) -> None:
    remove_path(link_path)
    link_path.parent.mkdir(parents=True, exist_ok=True)
    link_path.symlink_to(target, target_is_directory=target.is_dir())


def setup_persistent_links(
    base: Path,
    entries: Iterable[MapperEntry],
    *,
    base_subdirs: Optional[Iterable[str]] = None,
) -> None:
    base = base.expanduser().resolve()
    ensure_dir(base)

    if base_subdirs:
        for subdir in base_subdirs:
            ensure_dir(base / subdir)

    for persistent_subdir, local_link in entries:
        persistent_target = base / persistent_subdir
        ensure_dir(persistent_target)
        force_symlink(persistent_target, local_link.expanduser())


def _normalize_use_mapper(
    use_mapper: Optional[Iterable[str]], default_mapper: str
) -> List[str]:
    if use_mapper is None:
        return [default_mapper]

    if isinstance(use_mapper, str):
        mapper_names = [use_mapper]
    else:
        mapper_names = list(use_mapper)

    if not mapper_names:
        return [default_mapper]

    return mapper_names


def _normalize_extra_mappers(extra_mappers: ExtraMappers) -> List[MapperEntry]:
    if extra_mappers is None:
        return []

    if isinstance(extra_mappers, Mapping):
        items = list(extra_mappers.items())
    elif (
        isinstance(extra_mappers, tuple)
        and len(extra_mappers) == 2
        and isinstance(extra_mappers[0], str)
    ):
        items = [extra_mappers]
    else:
        items = list(extra_mappers)

    normalized: List[MapperEntry] = []
    for item in items:
        if not isinstance(item, (tuple, list)) or len(item) != 2:
            raise ValueError(
                "extra_mappers must be a dict or iterable of (name, local_path) pairs"
            )
        persistent_name, local_path = item
        if not isinstance(persistent_name, str):
            raise ValueError("extra_mappers names must be strings")
        normalized.append((persistent_name, Path(str(local_path)).expanduser()))

    return normalized


def resolve_mapper_entries(
    *,
    use_mapper: Optional[Iterable[str]],
    default_mapper: str,
    extra_mappers: ExtraMappers,
) -> List[MapperEntry]:
    mapper_names = _normalize_use_mapper(use_mapper, default_mapper)

    entries_by_name: Dict[str, Path] = {}
    for mapper_name in mapper_names:
        if mapper_name not in PRESET_MAPPERS:
            supported = ", ".join(sorted(PRESET_MAPPERS.keys()))
            raise ValueError(
                f"Unsupported mapper preset '{mapper_name}'. Supported: {supported}"
            )
        for persistent_name, local_path in PRESET_MAPPERS[mapper_name]:
            entries_by_name[persistent_name] = Path(local_path).expanduser()

    for persistent_name, local_path in _normalize_extra_mappers(extra_mappers):
        entries_by_name[persistent_name] = local_path

    return list(entries_by_name.items())


def setup_editor_mappers(
    runtime_dir: Path,
    *,
    default_mapper: str,
    use_mapper: Optional[Iterable[str]] = None,
    extra_mappers: ExtraMappers = None,
) -> List[MapperEntry]:
    entries = resolve_mapper_entries(
        use_mapper=use_mapper,
        default_mapper=default_mapper,
        extra_mappers=extra_mappers,
    )
    setup_persistent_links(
        base=runtime_dir,
        base_subdirs=[entry[0] for entry in entries],
        entries=entries,
    )
    return entries
