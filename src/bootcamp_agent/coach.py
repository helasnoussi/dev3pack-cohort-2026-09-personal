"""Ask the course a question, from inside the notebook, with no assistant at all.

    from bootcamp_agent.coach import coach
    coach("how do I hand my work in?")

WHY THIS IS NOT AN MCP CLIENT. MCP is spoken by a HOST -- Claude Code, Claude
Desktop, Cursor -- and there is no host inside a Jupyter kernel. A notebook that
"uses MCP" would be a notebook pretending. So the same retrieval runs here in
process, and the MCP server exists separately for the learner's own assistant.
One engine, two surfaces, neither imitating the other.

WHAT IT CAN AND CANNOT DO. It quotes pages that exist in YOUR clone and names
them. It cannot answer about a week that has not been published -- that is a
property, not a limitation, and it is why the answer says which page it came
from: a page id is something you can open, which a confident paraphrase is not.

NO NETWORK, NO KEY, NO MODEL. This is the navigator layer only: retrieval over
course pages, quoted verbatim. Measured against three local models on the same
passages, a 7-8B model adds fluent prose and a 1B model refuses outright -- so
prose is worth having but is never the part you can rely on. The passages are.

RETRIEVED TEXT IS DATA, NEVER INSTRUCTIONS. Session 4 teaches this and the coach
obeys it: nothing read out of a page is executed, followed, or passed to a tool.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from bootcamp_agent.documents import Document
from bootcamp_agent.retrieval import ScoredChunk, retrieve

#: `extract_questions` leaves these where a quiz block was. They are not prose
#: and a learner who retrieves one has been shown machinery, not an answer.
_PLACEHOLDER = re.compile(r"QUESTIONPLACEHOLDER\d+")

#: A quiz answer must never be retrievable. The blocks are stripped, and this is
#: the belt to that brace: a page whose id says "quiz" is not in the corpus.
_NEVER = ("quiz",)


def course_documents(units_root: Path | None = None) -> list[Document]:
    """Every published page in this clone, as retrieval documents.

    Built per call and never cached to disk: an index that can go stale is worse
    than no index, and the corpus is small enough that this is instant.

    Entries are filtered on `source.is_file()` because `read.entries()` lists the
    whole course, including weeks that have not been published into a student's
    clone yet. That filter is what makes "it only answers about what you have"
    true rather than hoped for.
    """
    from bootcamp_agent import read

    documents: list[Document] = []
    for entry in read.entries():
        if any(word in entry.local for word in _NEVER) or not entry.source.is_file():
            continue
        text, _ = read.extract_questions(entry.source.read_text(encoding="utf-8"))
        text = _PLACEHOLDER.sub("", text).strip()
        if not text:
            continue
        documents.append(
            Document(
                doc_id=entry.local,
                title=entry.title,
                text=text,
                source=str(entry.source),
                tags=(entry.group,),
            )
        )
    return documents


@dataclass(frozen=True)
class Answer:
    """What the pages say, and which pages said it."""

    question: str
    passages: tuple[ScoredChunk, ...]
    #: doc_id -> page title. A `Chunk` carries only the id, and an id alone
    #: ("unit0/how-to-submit") is navigable but not readable; the pair is both.
    titles: dict[str, str]

    @property
    def refused(self) -> bool:
        return not self.passages

    def __str__(self) -> str:
        if self.refused:
            return (
                "NOT IN THESE PAGES.\n"
                "Nothing in your clone shares a word with that question. Either the\n"
                "course does not cover it, or its week has not been published yet —\n"
                "`git pull` on a Monday is what brings the next one."
            )
        lines = []
        for scored in self.passages:
            chunk = scored.chunk
            title = self.titles.get(chunk.doc_id, chunk.doc_id)
            lines.append(f"--- {title}  [{chunk.doc_id}]")
            lines.append(chunk.text.strip())
            lines.append("")
        return "\n".join(lines).rstrip()


def ask(
    question: str,
    top_k: int = 3,
    documents: list[Document] | None = None,
    max_chars: int = 800,
) -> Answer:
    """The passages that answer a question, each labelled with its page id.

    `max_chars` is how large a chunk the retriever scores, and it is exposed
    here because it is a knob worth turning: measured on the labelled set, 800
    scores 18/25 and 400 scores 19/25. The curve is not monotonic -- 300 is
    worse than both -- which is the reason the bonus unit makes you measure
    rather than reason about it.
    """
    corpus = course_documents() if documents is None else documents
    return Answer(
        question=question,
        passages=tuple(retrieve(question, corpus, top_k=top_k, max_chars=max_chars)),
        titles={doc.doc_id: doc.title for doc in corpus},
    )


def coach(question: str, top_k: int = 3, max_chars: int = 800) -> None:
    """Print the answer. The notebook-shaped entry point, so nothing is returned."""
    print(ask(question, top_k=top_k, max_chars=max_chars))


__all__ = ["Answer", "ask", "coach", "course_documents"]
