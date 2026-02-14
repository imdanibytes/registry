#!/usr/bin/env python3
"""Build the compiled index.json from per-package YAML files.

Reads registry.yaml for metadata, scans plugins/ and extensions/ for
individual package YAML files, validates each against its JSON schema,
filters out unlisted entries, and writes index.json.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

try:
    import referencing
    import referencing.jsonschema
    from jsonschema import Draft7Validator
except ImportError:
    print("ERROR: jsonschema and referencing are required. Install with: pip install jsonschema", file=sys.stderr)
    sys.exit(1)


def load_yaml(path: Path) -> dict:
    with open(path) as f:
        data = yaml.safe_load(f)
    if isinstance(data, dict):
        _stringify_scalars(data)
    return data


def _stringify_scalars(d: dict) -> None:
    """Convert non-string scalars back to strings where the schema expects strings.

    PyYAML auto-parses ISO timestamps as datetime and bare versions as floats.
    The JSON schemas declare these as type: string, so we normalize here.
    """
    from datetime import date, datetime

    for key, value in d.items():
        if isinstance(value, (datetime, date)):
            d[key] = value.isoformat()
        elif isinstance(value, float) and key in ("version",):
            d[key] = str(value)


def load_schema(schema_dir: Path, filename: str) -> dict:
    with open(schema_dir / filename) as f:
        return json.load(f)


def validate_entry(entry: dict, schema: dict, registry: referencing.Registry, filepath: Path) -> list[str]:
    """Validate a single entry against a schema. Returns list of error messages."""
    validator = Draft7Validator(schema, registry=registry)
    errors = []
    for error in sorted(validator.iter_errors(entry), key=lambda e: list(e.path)):
        path = ".".join(str(p) for p in error.absolute_path) or "(root)"
        errors.append(f"  {filepath}: {path}: {error.message}")
    return errors


def scan_packages(directory: Path, schema: dict, registry: referencing.Registry, kind: str) -> tuple[list[dict], list[str]]:
    """Scan a directory for YAML package files and validate them.

    Returns (entries, errors) where entries excludes unlisted packages.
    """
    entries = []
    errors = []
    seen_ids = set()

    yaml_files = sorted(directory.glob("*.yaml"))
    if not yaml_files and kind == "plugin":
        errors.append(f"WARNING: No {kind} YAML files found in {directory}")

    for filepath in yaml_files:
        try:
            entry = load_yaml(filepath)
        except yaml.YAMLError as e:
            errors.append(f"  {filepath}: invalid YAML: {e}")
            continue

        if entry is None:
            errors.append(f"  {filepath}: empty file")
            continue

        # Validate against schema
        entry_errors = validate_entry(entry, schema, registry, filepath)
        errors.extend(entry_errors)

        if entry_errors:
            continue

        # Check for duplicate IDs
        pkg_id = entry.get("id", "")
        if pkg_id in seen_ids:
            errors.append(f"  {filepath}: duplicate {kind} ID '{pkg_id}'")
            continue
        seen_ids.add(pkg_id)

        # Check filename matches ID
        expected_filename = f"{pkg_id}.yaml"
        if filepath.name != expected_filename:
            errors.append(f"  {filepath}: filename must match ID (expected {expected_filename})")
            continue

        # Filter out unlisted entries
        if entry.get("status") != "unlisted":
            entries.append(entry)

    return entries, errors


def main():
    parser = argparse.ArgumentParser(description="Build Nexus registry index.json from YAML sources")
    parser.add_argument(
        "--registry-dir",
        type=Path,
        default=None,
        help="Path to the registry root directory (default: script's parent directory)",
    )
    args = parser.parse_args()

    registry_dir = args.registry_dir or Path(__file__).resolve().parent.parent
    registry_dir = registry_dir.resolve()

    # Verify structure exists
    registry_yaml = registry_dir / "registry.yaml"
    plugins_dir = registry_dir / "plugins"
    extensions_dir = registry_dir / "extensions"
    schema_dir = registry_dir / "schema"

    if not registry_yaml.exists():
        print(f"ERROR: {registry_yaml} not found", file=sys.stderr)
        sys.exit(1)

    # Load registry metadata
    try:
        registry_meta = load_yaml(registry_yaml)
    except yaml.YAMLError as e:
        print(f"ERROR: invalid registry.yaml: {e}", file=sys.stderr)
        sys.exit(1)

    # Load schemas
    plugin_schema = load_schema(schema_dir, "plugin.schema.json")
    extension_schema = load_schema(schema_dir, "extension.schema.json")

    # Build a referencing registry so $ref between schemas works
    schema_resources = []
    for schema_file in schema_dir.glob("*.json"):
        schema_data = load_schema(schema_dir, schema_file.name)
        resource = referencing.Resource.from_contents(schema_data, default_specification=referencing.jsonschema.DRAFT7)
        schema_resources.append((schema_file.name, resource))
    ref_registry = referencing.Registry().with_resources(schema_resources)

    all_errors = []

    # Scan plugins
    plugins, plugin_errors = scan_packages(plugins_dir, plugin_schema, ref_registry, "plugin")
    all_errors.extend(plugin_errors)

    # Scan extensions
    extensions = []
    extension_errors = []
    if extensions_dir.exists():
        extensions, extension_errors = scan_packages(extensions_dir, extension_schema, ref_registry, "extension")
        all_errors.extend(extension_errors)

    # Check for cross-type ID collisions
    plugin_ids = {p["id"] for p in plugins}
    extension_ids = {e["id"] for e in extensions}
    collisions = plugin_ids & extension_ids
    if collisions:
        for cid in collisions:
            all_errors.append(f"  ID '{cid}' exists as both a plugin and an extension")

    # Report errors
    if all_errors:
        print("Validation errors:", file=sys.stderr)
        for err in all_errors:
            print(err, file=sys.stderr)
        sys.exit(1)

    # Build index
    index = {
        "version": 2,
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "registry": registry_meta,
        "plugins": plugins,
        "extensions": extensions,
    }

    output_path = registry_dir / "index.json"
    with open(output_path, "w") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Built {output_path}")
    print(f"  {len(plugins)} plugin(s), {len(extensions)} extension(s)")


if __name__ == "__main__":
    main()
