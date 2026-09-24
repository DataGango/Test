"""The model-facing side of the agent: planning and writing code with Claude."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field

from .languages import Language

MODEL = "claude-opus-5"

SYSTEM_PROMPT = """You are a careful software engineer. You write complete, working, \
self-contained source files. Never leave placeholders or TODOs in place of real code."""


class Plan(BaseModel):
    steps: list[str] = Field(description="Short, ordered implementation steps")


class CodeFile(BaseModel):
    filename: str = Field(description="File name including extension, no directories")
    code: str = Field(description="Complete contents of the source file")


class CodeWriter(Protocol):
    def plan(self, task: str, language: Language) -> Plan: ...

    def write(self, task: str, language: Language, plan: Plan) -> CodeFile: ...

    def fix(self, task: str, language: Language, current: CodeFile, errors: str) -> CodeFile: ...


class ClaudeRefusal(RuntimeError):
    """Raised when Claude declines the request."""


class ClaudeCodeWriter:
    """CodeWriter backed by the Claude API. Reads credentials from the environment."""

    def __init__(self, model: str = MODEL, effort: str = "high") -> None:
        import anthropic

        self.client = anthropic.Anthropic()
        self.model = model
        self.effort = effort

    def _ask(self, prompt: str, output: type[BaseModel]) -> BaseModel:
        response = self.client.messages.parse(
            model=self.model,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            thinking={"type": "adaptive"},
            output_config={"effort": self.effort},
            output_format=output,
            messages=[{"role": "user", "content": prompt}],
            # Re-run declined requests on Anthropic's recommended fallback model.
            extra_headers={"anthropic-beta": "server-side-fallback-2026-07-01"},
            extra_body={"fallbacks": "default"},
        )
        if response.stop_reason == "refusal":
            raise ClaudeRefusal("Claude declined this request")
        if response.stop_reason == "max_tokens" or response.parsed_output is None:
            raise RuntimeError(f"incomplete response (stop_reason={response.stop_reason})")
        return response.parsed_output

    def plan(self, task: str, language: Language) -> Plan:
        prompt = (
            f"Task: {task}\n\nLanguage: {language.name}. {language.notes}\n\n"
            "Break the implementation into 3-8 short, ordered steps."
        )
        return self._ask(prompt, Plan)

    def write(self, task: str, language: Language, plan: Plan) -> CodeFile:
        steps = "\n".join(f"{i}. {s}" for i, s in enumerate(plan.steps, 1))
        prompt = (
            f"Task: {task}\n\nLanguage: {language.name}. {language.notes}\n\n"
            f"Follow this plan:\n{steps}\n\n"
            f"Write the complete program as one {language.extension} file."
        )
        return self._ask(prompt, CodeFile)

    def fix(self, task: str, language: Language, current: CodeFile, errors: str) -> CodeFile:
        prompt = (
            f"Task: {task}\n\nLanguage: {language.name}. {language.notes}\n\n"
            f"This file, {current.filename}, fails to compile:\n\n{current.code}\n\n"
            f"Compiler output:\n{errors}\n\n"
            "Return the corrected complete file."
        )
        return self._ask(prompt, CodeFile)
