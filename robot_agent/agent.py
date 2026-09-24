"""The robotic coding agent: turns a task into working code, one step at a time.

Steps:
  1. plan   - break the task into implementation steps
  2. write  - write the source file following the plan
  3. check  - compile / syntax-check it with the language's toolchain
  4. fix    - on failure, send the errors back and rewrite (repeats 3-4)
  5. save   - write the final file to the output directory
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from .languages import Language, get_language
from .writer import CodeFile, CodeWriter, Plan


@dataclass(frozen=True)
class StepResult:
    index: int
    name: str
    ok: bool
    message: str


@dataclass
class AgentResult:
    ok: bool
    file: CodeFile | None = None
    path: Path | None = None
    plan: Plan | None = None
    history: list[StepResult] = field(default_factory=list)


class CodingAgent:
    def __init__(
        self,
        writer: CodeWriter,
        output_dir: str | Path = "output",
        max_fixes: int = 3,
        on_step: Callable[[StepResult], None] | None = None,
    ) -> None:
        self.writer = writer
        self.output_dir = Path(output_dir)
        self.max_fixes = max_fixes
        self.on_step = on_step

    def run(self, task: str, language: str | Language) -> AgentResult:
        lang = get_language(language) if isinstance(language, str) else language
        result = AgentResult(ok=False)

        def record(name: str, ok: bool, message: str) -> None:
            step = StepResult(len(result.history) + 1, name, ok, message)
            result.history.append(step)
            if self.on_step:
                self.on_step(step)

        result.plan = self.writer.plan(task, lang)
        record("plan", True, "\n".join(f"- {s}" for s in result.plan.steps))

        code = self._normalize(self.writer.write(task, lang, result.plan), lang)
        record("write", True, f"wrote {code.filename} ({len(code.code.splitlines())} lines)")

        for attempt in range(self.max_fixes + 1):
            check = lang.check(code.filename, code.code)
            record("check", check.ok, check.output or "no errors")
            if check.ok:
                break
            if attempt == self.max_fixes:
                result.file = code
                return result
            code = self._normalize(self.writer.fix(task, lang, code, check.output), lang)
            record("fix", True, f"rewrote {code.filename} (attempt {attempt + 1})")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / code.filename
        path.write_text(code.code)
        record("save", True, f"saved {path}")
        result.ok, result.file, result.path = True, code, path
        return result

    @staticmethod
    def _normalize(code: CodeFile, lang: Language) -> CodeFile:
        """Keep the file inside the output directory and give it the right extension."""
        name = Path(code.filename).name or "main"
        if not name.endswith(lang.extension):
            name = Path(name).stem + lang.extension
        return CodeFile(filename=name, code=code.code)
