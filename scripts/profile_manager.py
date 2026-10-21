#!/usr/bin/env python3
"""Manage a local, non-sensitive reimbursement profile."""

from __future__ import annotations

import argparse
import copy
import json
import os
import tempfile
from pathlib import Path
from typing import Any


SENSITIVE_KEY_PARTS = {
    "password",
    "passwd",
    "token",
    "secret",
    "api_key",
    "apikey",
    "cookie",
    "authorization",
}

REQUIRED_TEXT_PATHS = (
    ("profile_name",),
    ("claimant", "name"),
    ("organization", "name"),
    ("storage", "default_output_dir"),
    ("mail", "provider"),
    ("rules", "base_currency"),
    ("rules", "preset"),
)

ALLOWED_FIELDS = {
    (): {
        "schema_version",
        "profile_name",
        "claimant",
        "organization",
        "storage",
        "mail",
        "rules",
    },
    ("claimant",): {"name", "travellers"},
    ("organization",): {"name", "invoice_title", "tax_id"},
    ("storage",): {"default_output_dir"},
    ("mail",): {"provider", "folders"},
    ("rules",): {"base_currency", "categories", "custom", "preset"},
}

SKILL_ROOT = Path(__file__).resolve().parents[1]


def resolve_profile_path(path: Path) -> Path:
    """Resolve an absolute profile path and keep it outside the Skill."""
    expanded = path.expanduser()
    if not expanded.is_absolute():
        raise ValueError("profile path must be absolute")
    resolved = expanded.resolve(strict=False)
    try:
        resolved.relative_to(SKILL_ROOT)
    except ValueError:
        return resolved
    raise ValueError("profile path must be outside the Skill directory")


def default_profile_path() -> Path:
    """Return the configured profile path or the safe per-user default."""
    override = os.environ.get("REIMBURSEMENT_PROFILE_PATH")
    if override:
        return resolve_profile_path(Path(override))
    return resolve_profile_path(
        Path.home()
        / ".codex"
        / "reimbursement-material-organizer"
        / "profile.json"
    )


def _value_at(data: dict[str, Any], path: tuple[str, ...]) -> Any:
    value: Any = data
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    compact = normalized.replace("_", "")
    return any(compact.endswith(part.replace("_", "")) for part in SENSITIVE_KEY_PARTS)


def _find_sensitive_keys(value: Any, prefix: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{prefix}.{key}" if prefix else key
            if _is_sensitive_key(key):
                found.append(child_path)
            found.extend(_find_sensitive_keys(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_find_sensitive_keys(child, f"{prefix}[{index}]"))
    return found


def _validate_allowed_fields(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for path, allowed in ALLOWED_FIELDS.items():
        value: Any = data if not path else _value_at(data, path)
        label = ".".join(path) or "profile"
        if not isinstance(value, dict):
            if path:
                errors.append(f"{label} must be an object")
            continue
        for key in value:
            if key not in allowed:
                field = ".".join((*path, key))
                errors.append(f"unknown field: {field}")
    return errors


def _is_string_list(value: Any, allow_empty: bool = True) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(isinstance(item, str) and item.strip() for item in value)
    )


def validate_profile(data: dict[str, Any]) -> list[str]:
    """Return validation errors; an empty list means the profile is valid."""
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["profile must be a JSON object"]

    errors.extend(_validate_allowed_fields(data))

    if type(data.get("schema_version")) is not int or data.get("schema_version") != 1:
        errors.append("schema_version must equal 1")

    for path in REQUIRED_TEXT_PATHS:
        value = _value_at(data, path)
        label = ".".join(path)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{label} must be a non-empty string")

    optional_text_paths = (
        ("organization", "invoice_title"),
        ("organization", "tax_id"),
    )
    for path in optional_text_paths:
        value = _value_at(data, path)
        if value is not None and not isinstance(value, str):
            errors.append(f"{'.'.join(path)} must be a string")

    optional_list_paths = (
        ("claimant", "travellers"),
        ("mail", "folders"),
        ("rules", "custom"),
    )
    for path in optional_list_paths:
        value = _value_at(data, path)
        if value is not None and not _is_string_list(value):
            errors.append(f"{'.'.join(path)} must be a string list")

    categories = _value_at(data, ("rules", "categories"))
    if not _is_string_list(categories, allow_empty=False):
        errors.append("rules.categories must be a non-empty string list")

    preset = _value_at(data, ("rules", "preset"))
    if preset not in {"none", "hutong"}:
        errors.append("rules.preset must be one of: none, hutong")

    for key_path in _find_sensitive_keys(data):
        errors.append(f"sensitive field is not allowed: {key_path}")

    return errors


def load_profile(path: Path | None = None) -> dict[str, Any]:
    """Read and validate a profile."""
    target = resolve_profile_path(path) if path is not None else default_profile_path()
    with target.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    errors = validate_profile(data)
    if errors:
        raise ValueError("; ".join(errors))
    return data


def profile_summary(data: dict[str, Any]) -> dict[str, Any]:
    """Return a display-safe copy of a validated profile."""
    errors = validate_profile(data)
    if errors:
        raise ValueError("; ".join(errors))
    summary = copy.deepcopy(data)
    tax_id = summary["organization"].get("tax_id", "")
    if tax_id:
        summary["organization"]["tax_id"] = "***已隐藏***"
    return summary


def save_profile(
    data: dict[str, Any], path: Path | None = None, force: bool = False
) -> Path:
    """Validate and atomically save a private profile file."""
    errors = validate_profile(data)
    if errors:
        raise ValueError("; ".join(errors))

    target = resolve_profile_path(path) if path is not None else default_profile_path()
    if target.exists() and not force:
        raise FileExistsError(f"profile already exists: {target}")

    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=target.parent,
            delete=False,
        ) as handle:
            temporary_name = handle.name
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.chmod(temporary_name, 0o600)
        if force:
            os.replace(temporary_name, target)
        else:
            try:
                os.link(temporary_name, target)
            except FileExistsError as error:
                raise FileExistsError(f"profile already exists: {target}") from error
            os.unlink(temporary_name)
        temporary_name = ""
        os.chmod(target, 0o600)
    finally:
        if temporary_name and os.path.exists(temporary_name):
            os.unlink(temporary_name)

    return target


def _read_json(path: str) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, help="override profile path")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("path", help="show the profile path")
    subparsers.add_parser("show", help="show the validated profile")

    validate_parser = subparsers.add_parser(
        "validate", help="validate a profile JSON file"
    )
    validate_parser.add_argument("source")

    save_parser = subparsers.add_parser("save", help="save a profile JSON file")
    save_parser.add_argument("source")
    save_parser.add_argument("--force", action="store_true")

    args = parser.parse_args()
    target = (
        resolve_profile_path(args.profile)
        if args.profile is not None
        else default_profile_path()
    )

    if args.command == "path":
        print(target)
        return 0

    if args.command == "show":
        print(
            json.dumps(
                profile_summary(load_profile(target)),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    data = _read_json(args.source)
    errors = validate_profile(data)
    if errors:
        for error in errors:
            print(error)
        return 1

    if args.command == "validate":
        print("profile is valid")
        return 0

    print(save_profile(data, target, force=args.force))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
