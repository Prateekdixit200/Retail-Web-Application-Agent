"""PreToolUse hook script: validates run_command tool calls.

Reads the tool call payload from stdin (JSON), inspects the CommandLine
argument, and blocks destructive commands. Returns a JSON decision on stdout.

Decision values:
  - "allow"    : Let the command proceed automatically.
  - "deny"     : Hard-block the command immediately.
  - "ask"      : Prompt the user for confirmation.
"""

import json
import re
import sys

# Patterns that match destructive or dangerous shell commands.
# Each entry is a tuple of (compiled_regex, human-readable_reason).
BLOCKED_PATTERNS = [
    (
        re.compile(r"\brm\s+.*-\s*[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\b"),
        "Recursive force-delete (rm -rf) is blocked.",
    ),
    (
        re.compile(r"\brm\s+.*-\s*[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*\b"),
        "Recursive force-delete (rm -fr) is blocked.",
    ),
    (
        re.compile(r"\bmkfs\b"),
        "Filesystem formatting (mkfs) is blocked.",
    ),
    (
        re.compile(r"\bdd\s+.*of\s*=\s*/dev/"),
        "Raw disk write (dd to /dev/) is blocked.",
    ),
    (
        re.compile(r">\s*/dev/sd[a-z]"),
        "Direct write to block device is blocked.",
    ),
    (
        re.compile(r"\bchmod\s+.*-\s*[a-zA-Z]*R[a-zA-Z]*\s+777\b"),
        "Recursive world-writable permissions (chmod -R 777) is blocked.",
    ),
    (
        re.compile(r":()\s*\{\s*:\|\:&\s*\}\s*;:"),
        "Fork bomb detected and blocked.",
    ),
]


def validate(payload: dict) -> dict:
    """Inspect the tool call payload and return an allow/deny decision."""
    tool_call = payload.get("toolCall", {})
    tool_name = tool_call.get("name", "")

    # Only gate run_command calls; allow everything else.
    if tool_name != "run_command":
        return {"decision": "allow"}

    command_line = tool_call.get("args", {}).get("CommandLine", "")

    if not command_line.strip():
        return {
            "decision": "deny",
            "reason": "Empty command line is not permitted.",
        }

    for pattern, reason in BLOCKED_PATTERNS:
        if pattern.search(command_line):
            return {
                "decision": "deny",
                "reason": f"Blocked: {reason} Command: {command_line}",
            }

    # Command passed all checks.
    return {"decision": "allow"}


def main():
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        # If we can't parse the input, deny by default (fail-closed).
        result = {
            "decision": "deny",
            "reason": "Hook received invalid JSON on stdin.",
        }
        json.dump(result, sys.stdout)
        sys.exit(0)

    result = validate(payload)
    json.dump(result, sys.stdout)
    sys.exit(0)


if __name__ == "__main__":
    main()
