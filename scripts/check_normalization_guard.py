from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable
from typing import Any

try:
    from scripts._bootstrap import PROJECT_ROOT
    from scripts._normalization_guard import build_command
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from _bootstrap import PROJECT_ROOT
    from _normalization_guard import build_command

ROOT = PROJECT_ROOT

Runner = Callable[..., subprocess.CompletedProcess[Any]]


def main(argv: list[str] | None = None, *, runner: Runner = subprocess.run) -> int:
    if argv:
        print("check_normalization_guard.py does not accept positional arguments.", flush=True)
        return 2
    command = build_command()
    print("Running normalization guard:", flush=True)
    print(subprocess.list2cmdline(command), flush=True)
    return int(runner(command, cwd=ROOT, check=False).returncode)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
