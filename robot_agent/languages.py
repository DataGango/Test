"""Supported target languages and how to compile-check code written in them."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CheckResult:
    ok: bool
    output: str
    skipped: bool = False


@dataclass(frozen=True)
class Language:
    name: str
    extension: str
    tool: str  # executable required for the check
    check_args: tuple[str, ...]  # arguments passed after the tool, before the file
    notes: str  # extra conventions given to the model

    def check(self, filename: str, code: str, timeout: float = 60) -> CheckResult:
        """Compile or syntax-check the code in a scratch directory."""
        exe = shutil.which(self.tool)
        if exe is None:
            return CheckResult(True, f"{self.tool} not installed; check skipped", skipped=True)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / Path(filename).name
            path.write_text(code)
            try:
                proc = subprocess.run(
                    [exe, *self.check_args, path.name],
                    cwd=tmp,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
            except subprocess.TimeoutExpired:
                return CheckResult(False, f"{self.tool} timed out after {timeout}s")
        output = (proc.stdout + proc.stderr).strip()
        return CheckResult(proc.returncode == 0, output)


LANGUAGES: dict[str, Language] = {
    "python": Language(
        name="Python",
        extension=".py",
        tool="python3",
        check_args=("-m", "py_compile"),
        notes="Target Python 3.10+. Use only the standard library unless asked otherwise.",
    ),
    "c": Language(
        name="C",
        extension=".c",
        tool="gcc",
        check_args=("-std=c11", "-Wall", "-Wextra", "-fsyntax-only"),
        notes="Target C11. Use only the C standard library. Include a main() when the task is a program.",
    ),
    "java": Language(
        name="Java",
        extension=".java",
        tool="javac",
        check_args=("-d", "."),
        notes="Target Java 17. The filename must match the single public class name.",
    ),
    "typescript": Language(
        name="TypeScript",
        extension=".ts",
        tool="tsc",
        check_args=("--noEmit", "--strict", "--target", "es2022", "--module", "nodenext"),
        notes="Target strict TypeScript for Node.js; avoid third-party packages.",
    ),
}

ALIASES = {"py": "python", "ts": "typescript", "jva": "java"}


def get_language(key: str) -> Language:
    key = ALIASES.get(key.lower(), key.lower())
    try:
        return LANGUAGES[key]
    except KeyError:
        raise ValueError(f"unsupported language {key!r}; choose from {', '.join(LANGUAGES)}") from None
