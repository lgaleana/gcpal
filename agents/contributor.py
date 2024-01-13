from typing import List

from pydantic import BaseModel, Field

from ai import llm
from utils.state import Conversation


class Action:
    WRITE_COMMIT = "write_commit"


class File(BaseModel):
    path: str = Field(description="Path of the file")
    content: str = Field(description="Content of the file. Add a new line at the end.")

    def __str__(self) -> str:
        return f"{self.path}\n```\n{self.content}\n```"


class WriteCommitParams(BaseModel):
    message: str = Field(description="Commit message")
    files: List[File] = Field(description="New/edited files in the PR")
    test_files: List[File] = Field(
        description="New/edited files for the tests in the PR"
    )
    deleted_files: List[str] = Field(
        [], description="Paths of the files to delete, if any"
    )

    def __str__(self) -> str:
        new_files = "\n\n".join(str(f) for f in self.files)
        test_files = "\n\n".join(str(f) for f in self.test_files)
        deleted_files = "\n".join(self.deleted_files)
        return (
            f"{self.message}\n"
            f"{new_files}\n\n"
            f"{test_files}\n\n"
            f"{deleted_files}\n\n"
        )


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": Action.WRITE_COMMIT,
            "description": "Writes a commit to be pushed to the Pull Request",
            "parameters": WriteCommitParams.schema(),
        },
    },
]


PROMPT = """Pull Request 6 was created successfully.

### New Instructions

1. Improve upon the PR.
2. Use the best software engineering practices.
3. Pay attention to every comment and address it.
4. When ready, make the change. No need to ask for my confirmation."""


def next_action(
    conversation_context: Conversation,
    conversation: Conversation,
):
    next = llm.stream_next(
        conversation_context + [{"role": "user", "content": PROMPT}] + conversation,
        tools=TOOLS,
    )
    return next
