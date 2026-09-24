# Test

## Robotic coding agent

`robot_agent` is an agent that writes code for you in **Python, C, Java or TypeScript**, working through fixed steps:

1. **plan**: Claude breaks the task into implementation steps
2. **write**: Claude writes one complete source file that follows the plan
3. **check**: the file is compiled or syntax-checked locally (`python3 -m py_compile`, `gcc -fsyntax-only`, `javac`, `tsc --noEmit --strict`)
4. **fix**: if the check fails, the compiler errors go back to Claude for a rewrite (steps 3–4 repeat up to `--max-fixes` times)
5. **save**: the final file is written to the output directory

### Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...        # or `ant auth login`
```

### Usage

```bash
python -m robot_agent --lang python "a CLI that counts word frequencies in a file"
python -m robot_agent --lang c "print the first 20 prime numbers"
python -m robot_agent --lang java "a bank account class with deposit/withdraw and a demo main"
python -m robot_agent --lang typescript "a function that deep-merges two objects, with examples"
```

Options: `-o/--out DIR` (default `output/`), `--max-fixes N` (default 3), `--model` (default `claude-opus-5`).

From Python:

```python
from robot_agent import ClaudeCodeWriter, CodingAgent

result = CodingAgent(ClaudeCodeWriter(), output_dir="output").run("fizzbuzz to 100", "c")
print(result.ok, result.path)
```

The check step skips any language whose compiler isn't installed.

### Tests

`python -m unittest`. The tests use a fake writer, so they need no API key.
