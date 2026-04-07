from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src" / "dead_by_dawn_sim"
DEFAULT_MAX_LINES = 300
LINE_LIMIT_OVERRIDES = {}


def main() -> int:
    failures: list[str] = []
    for path in sorted(SRC_DIR.glob("*.py")):
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        limit = LINE_LIMIT_OVERRIDES.get(path.name, DEFAULT_MAX_LINES)
        if line_count > limit:
            failures.append(f"{path.relative_to(ROOT)} has {line_count} lines (limit: {limit})")

    if not failures:
        return 0

    print("Module size guard failed:")
    for failure in failures:
        print(f"  - {failure}")
    print("Refactor or raise the file-specific cap intentionally before growing these modules.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
