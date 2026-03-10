#!/usr/bin/env python3
"""Validate a JSON file against a JSON Schema.

Usage:
    validate-schema.py <schema_path> <json_path>
    validate-schema.py --dir <schema_path> <directory>

Exit codes:
    0 - valid
    1 - validation error
    2 - file/schema not found or parse error
"""
import json
import sys
from pathlib import Path

def validate_basic(schema: dict, data: dict, filepath: str) -> list[str]:
    """Basic schema validation without jsonschema library.

    Checks required fields, enum constraints, type constraints, and
    additionalProperties. Covers the most common validation needs.
    """
    errors = []

    # Check required fields
    for field in schema.get("required", []):
        if field not in data:
            errors.append(f"missing required field '{field}'")

    props = schema.get("properties", {})

    # Check additionalProperties
    if schema.get("additionalProperties") is False:
        allowed = set(props.keys())
        extra = set(data.keys()) - allowed
        if extra:
            errors.append(f"extra fields not allowed: {', '.join(sorted(extra))}")

    # Check each present field against its property definition
    for field, value in data.items():
        if field not in props:
            continue
        prop_def = props[field]

        # Type check
        expected_type = prop_def.get("type")
        if expected_type:
            if isinstance(expected_type, list):
                # Union type like ["string", "null"]
                type_ok = False
                for t in expected_type:
                    if t == "null" and value is None:
                        type_ok = True
                    elif t == "string" and isinstance(value, str):
                        type_ok = True
                    elif t == "integer" and isinstance(value, int) and not isinstance(value, bool):
                        type_ok = True
                    elif t == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
                        type_ok = True
                    elif t == "boolean" and isinstance(value, bool):
                        type_ok = True
                    elif t == "array" and isinstance(value, list):
                        type_ok = True
                    elif t == "object" and isinstance(value, dict):
                        type_ok = True
                if not type_ok:
                    errors.append(f"field '{field}' has wrong type: expected {expected_type}, got {type(value).__name__}")
            else:
                type_map = {
                    "string": str, "integer": int, "number": (int, float),
                    "boolean": bool, "array": list, "object": dict
                }
                if expected_type in type_map:
                    py_type = type_map[expected_type]
                    if expected_type == "null":
                        if value is not None:
                            errors.append(f"field '{field}' must be null")
                    elif not isinstance(value, py_type):
                        errors.append(f"field '{field}' has wrong type: expected {expected_type}")
                    elif expected_type in ("integer", "number") and isinstance(value, bool):
                        errors.append(f"field '{field}' has wrong type: expected {expected_type}")

        # Enum check
        if "enum" in prop_def and value is not None:
            if value not in prop_def["enum"]:
                errors.append(f"field '{field}' value '{value}' not in enum {prop_def['enum']}")

        # Pattern check for strings
        if "pattern" in prop_def and isinstance(value, str):
            import re
            if not re.match(prop_def["pattern"], value):
                errors.append(f"field '{field}' value '{value}' does not match pattern '{prop_def['pattern']}'")

    return errors


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)

    validate_dir = sys.argv[1] == "--dir"
    if validate_dir:
        schema_path = Path(sys.argv[2])
        target_dir = Path(sys.argv[3])
    else:
        schema_path = Path(sys.argv[1])
        target_path = Path(sys.argv[2])

    # Load schema
    if not schema_path.exists():
        print(f"Schema not found: {schema_path}", file=sys.stderr)
        sys.exit(2)

    try:
        schema = json.loads(schema_path.read_text())
    except json.JSONDecodeError as e:
        print(f"Invalid schema JSON: {e}", file=sys.stderr)
        sys.exit(2)

    # Determine files to validate
    if validate_dir:
        if not target_dir.is_dir():
            print(f"Directory not found: {target_dir}", file=sys.stderr)
            sys.exit(2)
        files = sorted(target_dir.glob("*.json"))
        files = [f for f in files if f.name != ".gitkeep"]
    else:
        if not target_path.exists():
            print(f"File not found: {target_path}", file=sys.stderr)
            sys.exit(2)
        files = [target_path]

    # Try to use jsonschema if available
    use_jsonschema = False
    try:
        import jsonschema
        use_jsonschema = True
    except ImportError:
        pass

    total_errors = 0
    for fp in files:
        try:
            data = json.loads(fp.read_text())
        except json.JSONDecodeError as e:
            print(f"FAIL {fp.name}: invalid JSON - {e}")
            total_errors += 1
            continue

        if use_jsonschema:
            try:
                jsonschema.validate(data, schema)
                print(f"PASS {fp.name}")
            except jsonschema.ValidationError as e:
                print(f"FAIL {fp.name}: {e.message}")
                total_errors += 1
        else:
            errors = validate_basic(schema, data, str(fp))
            if errors:
                for err in errors:
                    print(f"FAIL {fp.name}: {err}")
                total_errors += 1
            else:
                print(f"PASS {fp.name}")

    if total_errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
