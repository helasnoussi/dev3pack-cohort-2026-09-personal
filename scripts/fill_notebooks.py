"""Ship each session's notebook working, with the improvement named in the cell.

THE CHANGE THIS MAKES, and it is a change to what a hand-in means. Until now a
`TODO(you)` cell did not run: a learner wrote the answer or scored nothing. That
is a cliff, and on day one twenty-four of twenty-six people fell off it before
ever reaching a check.

Now every cell runs as shipped and every check passes on a clean clone. The
floor is "you ran it"; the ceiling is the improvement named at the top of each
cell, in the learner's own words, in their own notebook.

Mechanically this takes the solutions cell -- which is the code that passes --
and prefixes it with the specific thing worth improving. It never invents code:
a filled cell and its solution are the same lines.
"""

from __future__ import annotations

import sys
from pathlib import Path

import nbformat

ROOT = Path("/home/nan/PycharmProjects/Gecko/Dev3Pack-bootcamp-AI-Engineering")

#: One line per exercise, naming what a better version would do. Generic
#: encouragement is worse than nothing here -- "make it better" is not a task.
IMPROVE: dict[str, str] = {
    "ch02-e1": "add a fourth case that proves which keyword wins when a question contains both",
    "ch02-e2": "run each lane three times instead of two, and print WHICH reply differed",
    "ch02-e3": "make every sentence name a thing you could actually check tomorrow, not a category",
    "ch02-e4": (
        "carry the elapsed time into the trace, so a slow answer and a dead one look different"
    ),
    "ch03-e1": "add a field the model must leave empty when it does not know, and prove it does",
    "ch03-e2": "make the repair step say what it changed, not just that it changed something",
    "ch03-e3": "reject a confidence the citations do not support",
    "ch04-e1": (
        "name one argument the tool must refuse, and refuse it by shape rather than by value"
    ),
    "ch04-e2": "log the refusal with enough context to debug it, and nothing a key could hide in",
    "ch04-e3": "treat one more field of the tool output as untrusted, and say why that one",
    "ch05-e1": "stop on a budget you can see in the trace, not one buried in a constant",
    "ch05-e2": "make the repeated-call guard survive an argument that differs only in whitespace",
    "ch05-e3": (
        "record why the loop stopped, so a clean finish and a budget cut-off read differently"
    ),
    "ch05-e4": "make the safe stop return something the caller can act on, not just None",
}

BANNER = (
    "# ---------------------------------------------------------------------\n"
    "# THIS RUNS AS SHIPPED, and passes its check. That is the floor.\n"
    "# To stand above it: {improvement}.\n"
    "# Change it, re-run the check cell below, and keep what you learn.\n"
    "# ---------------------------------------------------------------------\n"
)


def exercise_of(cells, index: int) -> str | None:
    """The check id the next check cell names, which is what this cell answers."""
    import re

    for cell in cells[index + 1 : index + 4]:
        found = re.search(r'check\("(ch\d\d-e\d)"', cell.source)
        if found:
            return found.group(1)
    return None


def fill(session: Path) -> tuple[int, list[str]]:
    student_path = session / "notebook.ipynb"
    solutions_path = session / "solutions" / "notebook.ipynb"
    student = nbformat.read(student_path, as_version=4)
    solutions = nbformat.read(solutions_path, as_version=4)
    if len(student.cells) != len(solutions.cells):
        raise SystemExit(f"{session.name}: cell counts differ; refusing to guess the mapping")

    filled, missing = 0, []
    for index, cell in enumerate(student.cells):
        if cell.cell_type != "code" or "TODO(you)" not in cell.source:
            continue
        exercise = exercise_of(student.cells, index)
        if exercise is None or exercise not in IMPROVE:
            missing.append(f"{session.name} cell {index} -> {exercise}")
            continue
        cell.source = BANNER.format(improvement=IMPROVE[exercise]) + solutions.cells[index].source
        filled += 1

    if filled:
        nbformat.write(student, student_path)
    return filled, missing


def main() -> int:
    total, problems = 0, []
    for session in sorted((ROOT / "units/en/unit1").glob("session-*")):
        if not (session / "solutions" / "notebook.ipynb").is_file():
            continue
        filled, missing = fill(session)
        problems += missing
        total += filled
        print(f"{session.name}: {filled} cell(s) filled")
    for problem in problems:
        print(f"  NO IMPROVEMENT NAMED: {problem}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
