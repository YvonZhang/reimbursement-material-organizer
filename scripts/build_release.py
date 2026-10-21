#!/usr/bin/env python3
"""Build a deterministic, privacy-checked Skill release ZIP."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


ROOT_FILES = {"SKILL.md", "README.md", "LICENSE"}
ALLOWED_DIRECTORIES = {
    "agents": {".yaml"},
    "scripts": {".py"},
    "references": {".md"},
    "examples": {".md", ".json"},
    "tests": {".py"},
}
IGNORED_NAMES = {".DS_Store"}
IGNORED_PARTS = {"__pycache__"}
IGNORED_SUFFIXES = {".pyc"}
PROHIBITED_NAMES = {"profile.json"}
PROHIBITED_SUFFIXES = {
    ".pdf",
    ".ofd",
    ".xml",
    ".jpg",
    ".jpeg",
    ".png",
    ".heic",
}
PERSONAL_HOME_PATTERN = re.compile(rb"/(?:Users|home)/[^/\s\"']+")
SECRET_PATTERNS = (
    re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(rb"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(rb"\bBearer [A-Za-z0-9._-]{16,}\b"),
)
FIXED_ZIP_TIME = (2026, 1, 1, 0, 0, 0)


def _check_text_safety(path: Path, data: bytes) -> None:
    if PERSONAL_HOME_PATTERN.search(data):
        raise ValueError(f"personal home path is not allowed: {path}")
    for pattern in SECRET_PATTERNS:
        if pattern.search(data):
            raise ValueError(f"credential-like value is not allowed: {path}")


def collect_release_files(skill_root: Path) -> list[Path]:
    """Return privacy-checked files allowed in a release."""
    root = skill_root.resolve()
    if root.name != "reimbursement-material-organizer":
        raise ValueError("Skill directory must be named reimbursement-material-organizer")
    missing = sorted(name for name in ROOT_FILES if not (root / name).is_file())
    if missing:
        raise ValueError(f"missing required release files: {', '.join(missing)}")

    collected: list[Path] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if path.is_symlink():
            raise ValueError(f"symbolic links are not allowed: {relative}")
        if any(part in IGNORED_PARTS for part in relative.parts):
            continue
        if path.is_dir():
            continue
        if path.name in IGNORED_NAMES or path.suffix.lower() in IGNORED_SUFFIXES:
            continue
        if path.name.lower() in PROHIBITED_NAMES:
            raise ValueError(f"user profile is not allowed: {relative}")
        if path.suffix.lower() in PROHIBITED_SUFFIXES:
            raise ValueError(f"reimbursement material is not allowed: {relative}")

        if len(relative.parts) == 1:
            if relative.name not in ROOT_FILES:
                raise ValueError(f"unexpected root file: {relative}")
        else:
            top = relative.parts[0]
            allowed_suffixes = ALLOWED_DIRECTORIES.get(top)
            if allowed_suffixes is None or path.suffix.lower() not in allowed_suffixes:
                raise ValueError(f"unexpected release file: {relative}")

        data = path.read_bytes()
        _check_text_safety(relative, data)
        collected.append(path)

    return collected


def build_release(skill_root: Path, output: Path, force: bool = False) -> str:
    """Build the release and return its SHA-256 digest."""
    root = skill_root.resolve()
    target = output.expanduser().resolve(strict=False)
    if target.exists() and not force:
        raise FileExistsError(f"release already exists: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    files = collect_release_files(root)

    temporary_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            dir=target.parent,
            suffix=".zip",
            delete=False,
        ) as handle:
            temporary_name = handle.name

        with zipfile.ZipFile(
            temporary_name,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            for path in files:
                relative = path.relative_to(root)
                archive_name = PurePosixPath(root.name, relative.as_posix()).as_posix()
                info = zipfile.ZipInfo(archive_name, FIXED_ZIP_TIME)
                mode = 0o755 if relative.parts[0] == "scripts" else 0o644
                info.external_attr = mode << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, path.read_bytes(), compresslevel=9)

        os.replace(temporary_name, target)
        temporary_name = ""
    finally:
        if temporary_name and os.path.exists(temporary_name):
            os.unlink(temporary_name)

    return hashlib.sha256(target.read_bytes()).hexdigest()


def write_checksum(
    digest: str,
    release: Path,
    checksum: Path,
    force: bool = False,
) -> Path:
    """Atomically write a companion SHA-256 file."""
    target = checksum.expanduser().resolve(strict=False)
    if target.exists() and not force:
        raise FileExistsError(f"checksum already exists: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    content = f"{digest}  {release.name}\n"
    temporary_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=target.parent,
            delete=False,
        ) as handle:
            temporary_name = handle.name
            handle.write(content)
        os.replace(temporary_name, target)
        temporary_name = ""
    finally:
        if temporary_name and os.path.exists(temporary_name):
            os.unlink(temporary_name)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--checksum", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    digest = build_release(root, args.output, force=args.force)
    if args.checksum is not None:
        write_checksum(
            digest,
            args.output,
            args.checksum,
            force=args.force,
        )
    print(f"{digest}  {args.output.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
