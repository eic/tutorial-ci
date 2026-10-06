#!/usr/bin/env python3
"""Run the code blocks of a tutorial that are marked for CI.

Blocks are marked with the `ci` class in the fence attributes:

    ```{.bash .ci}                  run with bash
    ```{.python .ci}                run with python3
    ```{.cpp .ci file="Test.C"}     write to Test.C, run nothing

Blocks run in order (learners/setup.md, then episodes/*.md) in one working
directory, the way a learner would go through the tutorial.

Usage: run_blocks.py <tutorial directory> <working directory>
"""
import re
import subprocess
import sys
import textwrap
from pathlib import Path

FENCE = re.compile(r"^([ \t]*)```\{([^}]*)\}[ \t]*\n(.*?)^[ \t]*```", re.S | re.M)
RUNNERS = {"bash": ["bash", "-euo", "pipefail", "-c"], "python": ["python3", "-c"]}


def marked_blocks(markdown):
    """Yield (line number, classes, file name, code) for each block with the ci class."""
    text = markdown.read_text()
    for match in FENCE.finditer(text):
        attributes = match.group(2)
        classes = re.findall(r"\.([\w+-]+)", attributes)
        if "ci" not in classes:
            continue
        file_name = re.search(r'file="([^"]+)"', attributes)
        line = text.count("\n", 0, match.start()) + 1
        yield line, classes, file_name and file_name.group(1), textwrap.dedent(match.group(3))


def main(directory, work):
    work.mkdir(parents=True, exist_ok=True)
    sources = [directory / "learners" / "setup.md"] + sorted((directory / "episodes").glob("*.md"))
    count = 0
    for markdown in filter(Path.exists, sources):
        for line, classes, file_name, code in marked_blocks(markdown):
            count += 1
            location = f"{markdown.relative_to(directory)}:{line}"
            if file_name:
                (work / file_name).write_text(code)
                print(f"WROTE   {location}  {file_name}")
                continue
            language = next((name for name in classes if name in RUNNERS), None)
            if language is None:
                print(f"::error file={markdown.relative_to(directory)},line={line}::ci block needs .bash, .python or file=")
                return 1
            print(f"RUN     {location}\n{code}", flush=True)
            if subprocess.run(RUNNERS[language] + [code], cwd=work, stdin=subprocess.DEVNULL).returncode != 0:
                print(f"::error file={markdown.relative_to(directory)},line={line}::block failed")
                return 1
    print(f"{count} ci blocks")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]), Path(sys.argv[2]).resolve()))
