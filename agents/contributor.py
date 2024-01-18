from typing import List, Optional

from pydantic import BaseModel, Field

from agents.coder import File
from ai import llm
from tools.github import PullRequest
from utils.state import Conversation


class Action:
    AMEND_PR = "amend_pr"


class _AmendPRParams(BaseModel):
    title: str = Field(description="Commit message")
    description: Optional[str] = Field(
        None, description="New PR description, if it needs to change"
    )
    files: List[File] = Field(description="New/edited files in the PR")
    test_files: List[File] = Field(
        description="New/edited files for the tests in the PR"
    )
    deleted_files: List[str] = Field(
        [], description="Paths of the files to delete, if any"
    )

    def __str__(self) -> str:
        header = f"{self.title}\n"
        if self.description:
            header += f"{self.description}\n"
        new_files = "\n\n".join(str(f) for f in self.files)
        test_files = "\n\n".join(str(f) for f in self.test_files)
        deleted_files = "\n".join(self.deleted_files)
        return f"{header}\n{new_files}\n\n{test_files}\n\n{deleted_files}\n\n"


class AmendPRParams(_AmendPRParams):
    original: PullRequest


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": Action.AMEND_PR,
            "description": "Amend the Pull Request with a new commit",
            "parameters": _AmendPRParams.schema(),
        },
    },
]


PROMPT = """Pull Request {pr} was created successfully.

### New instructions

Amend the PR by writing new code. No need to wait for confirmation."""


def next_action(
    conversation_context: Conversation,
    conversation: Conversation,
    pr_number: int,
):
    next = llm.stream_next(
        conversation_context
        + [{"role": "user", "content": PROMPT.format(pr=pr_number)}]
        + conversation,
        tools=TOOLS,
    )
    return next
