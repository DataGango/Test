import shutil
import tempfile
import unittest
from pathlib import Path

from robot_agent import CodeFile, CodingAgent, Plan, get_language

GOOD = {
    "python": ("hello.py", 'print("hello")\n'),
    "c": ("hello.c", '#include <stdio.h>\nint main(void) { puts("hello"); return 0; }\n'),
    "java": (
        "Hello.java",
        'public class Hello { public static void main(String[] a) { System.out.println("hello"); } }\n',
    ),
    "typescript": ("hello.ts", 'const msg: string = "hello";\nconsole.log(msg);\n'),
}
BAD = {
    "python": "def f(:\n",
    "c": "int main(void) { return x; }\n",
    "java": "public class Hello { void f() { int x = \"s\"; } }\n",
    "typescript": 'const n: number = "not a number";\n',
}


class FakeWriter:
    """Returns scripted files so the agent loop can be tested without the API."""

    def __init__(self, files):
        self.files = list(files)
        self.fix_errors = []

    def plan(self, task, language):
        return Plan(steps=["write it"])

    def write(self, task, language, plan):
        return self.files.pop(0)

    def fix(self, task, language, current, errors):
        self.fix_errors.append(errors)
        return self.files.pop(0)


class LanguageCheckTests(unittest.TestCase):
    def test_good_and_bad_code(self):
        for key in GOOD:
            lang = get_language(key)
            with self.subTest(language=key):
                if shutil.which(lang.tool) is None:
                    self.skipTest(f"{lang.tool} not installed")
                filename, code = GOOD[key]
                self.assertTrue(lang.check(filename, code).ok)
                self.assertFalse(lang.check(filename, BAD[key]).ok)

    def test_aliases(self):
        self.assertEqual(get_language("ts").name, "TypeScript")
        self.assertEqual(get_language("jva").name, "Java")
        with self.assertRaises(ValueError):
            get_language("cobol")


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.out = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.out)

    def test_writes_and_saves(self):
        writer = FakeWriter([CodeFile(filename="hello.py", code='print("hi")\n')])
        result = CodingAgent(writer, self.out).run("say hi", "python")
        self.assertTrue(result.ok)
        self.assertEqual([s.name for s in result.history], ["plan", "write", "check", "save"])
        self.assertEqual((self.out / "hello.py").read_text(), 'print("hi")\n')

    def test_fixes_after_failed_check(self):
        writer = FakeWriter(
            [CodeFile(filename="a.py", code="def f(:\n"), CodeFile(filename="a.py", code="x = 1\n")]
        )
        result = CodingAgent(writer, self.out).run("task", "python")
        self.assertTrue(result.ok)
        self.assertEqual(
            [s.name for s in result.history], ["plan", "write", "check", "fix", "check", "save"]
        )
        self.assertIn("SyntaxError", writer.fix_errors[0])

    def test_gives_up_after_max_fixes(self):
        writer = FakeWriter([CodeFile(filename="a.py", code="def f(:\n")] * 3)
        result = CodingAgent(writer, self.out, max_fixes=2).run("task", "python")
        self.assertFalse(result.ok)
        self.assertEqual(sum(s.name == "fix" for s in result.history), 2)
        self.assertFalse(any(self.out.iterdir()))

    def test_filename_is_sanitized(self):
        writer = FakeWriter([CodeFile(filename="../../evil", code="x = 1\n")])
        result = CodingAgent(writer, self.out).run("task", "py")
        self.assertEqual(result.path, self.out / "evil.py")


if __name__ == "__main__":
    unittest.main()
