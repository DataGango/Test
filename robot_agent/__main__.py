"""Command line: python -m robot_agent --lang c "print the first 20 primes" """

import argparse
import sys

from .agent import CodingAgent, StepResult
from .languages import ALIASES, LANGUAGES
from .writer import MODEL, ClaudeCodeWriter


def main() -> int:
    parser = argparse.ArgumentParser(prog="robot_agent", description=__doc__)
    parser.add_argument("task", help="what the code should do")
    parser.add_argument("-l", "--lang", required=True, choices=[*LANGUAGES, *ALIASES])
    parser.add_argument("-o", "--out", default="output", help="output directory")
    parser.add_argument("--max-fixes", type=int, default=3)
    parser.add_argument("--model", default=MODEL)
    args = parser.parse_args()

    def report(step: StepResult) -> None:
        status = "ok " if step.ok else "ERR"
        print(f"step {step.index} [{status}] {step.name}")
        for line in step.message.splitlines():
            print(f"    {line}")

    agent = CodingAgent(ClaudeCodeWriter(model=args.model), args.out, args.max_fixes, report)
    result = agent.run(args.task, args.lang)
    if not result.ok:
        print("Could not produce code that compiles.", file=sys.stderr)
        return 1
    print(f"\nDone: {result.path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
