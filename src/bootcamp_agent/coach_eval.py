"""How good is the coach, as a number you can repeat.

    from bootcamp_agent.coach_eval import measure
    measure()

A change without its number is a preference, not an improvement. This is the
whole bar for the bonus unit and for any pull request against the coach: run it
before, change one thing, run it after, and report BOTH numbers including
whatever got worse.

WHAT IT MEASURES. Hit rate at top-k: for each labelled question, did any of the
pages we consider correct appear in the passages the retriever returned? That is
deliberately a weak metric -- it says nothing about whether the passage answers
the question, only that the right PAGE was reached. A stronger one is a fair
target for somebody's contribution.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from bootcamp_agent.coach import ask
from bootcamp_agent.documents import Document

DEFAULT_CASES = Path(__file__).resolve().parent.parent.parent / "data" / "evals" / "coach.jsonl"


class CaseError(Exception):
    """The labelled set could not be read."""


@dataclass(frozen=True)
class Case:
    question: str
    expected_doc_ids: tuple[str, ...]


@dataclass(frozen=True)
class Report:
    hits: int
    total: int
    misses: tuple[tuple[str, tuple[str, ...]], ...]

    @property
    def rate(self) -> float:
        return self.hits / self.total if self.total else 0.0

    def rendered(self) -> str:
        lines = [f"hit rate {self.hits}/{self.total} = {self.rate:.0%} (top-k)"]
        if self.misses:
            lines.append("")
            lines.append("missed:")
            for question, got in self.misses:
                found = ", ".join(got) if got else "nothing retrieved"
                lines.append(f"  {question}")
                lines.append(f"      got: {found}")
        return "\n".join(lines)


def load_cases(path: Path | None = None) -> list[Case]:
    source = path or DEFAULT_CASES
    if not source.is_file():
        raise CaseError(f"no labelled set at {source}")
    cases: list[Case] = []
    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise CaseError(f"{source}:{number}: {error}") from error
        cases.append(
            Case(question=row["question"], expected_doc_ids=tuple(row["expected_doc_ids"]))
        )
    return cases


def run(
    cases: list[Case],
    documents: list[Document] | None = None,
    top_k: int = 3,
    max_chars: int = 800,
) -> Report:
    hits, misses = 0, []
    for case in cases:
        answer = ask(case.question, top_k=top_k, documents=documents, max_chars=max_chars)
        got = tuple(dict.fromkeys(p.chunk.doc_id for p in answer.passages))
        if set(got) & set(case.expected_doc_ids):
            hits += 1
        else:
            misses.append((case.question, got))
    return Report(hits=hits, total=len(cases), misses=tuple(misses))


def measure(path: Path | None = None, top_k: int = 3, max_chars: int = 800) -> Report:
    """Print the number and every miss, and return the report."""
    report = run(load_cases(path), top_k=top_k, max_chars=max_chars)
    print(report.rendered())
    return report


__all__ = ["Case", "CaseError", "Report", "load_cases", "measure", "run"]
