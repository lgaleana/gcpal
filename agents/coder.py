from typing import List, Optional

from pydantic import BaseModel, Field

from ai import llm
from tools.github import GithubFile
from tools.jira import Issue
from utils.state import Conversation


class Action:
    WRITE_PR = "write_pr"


class File(BaseModel):
    path: str = Field(description="Path of the file")
    content: str = Field(description="Content of the file. Add a new line at the end.")

    def __str__(self) -> str:
        return f"{self.path}\n```\n{self.content}\n```"


class WritePRParams(BaseModel):
    title: str = Field(description="Title of the PR")
    description: str = Field(description="Description of the PR")
    files: List[File] = Field(description="New/edited files in the PR")
    test_files: List[File] = Field(
        description="New/edited files for the tests in the PR"
    )
    deleted_files: List[str] = Field(
        [], description="Paths of the files to delete, if any"
    )
    git_branch: str = Field(description="Name of the git branch for the new PR")

    def __str__(self) -> str:
        new_files = "\n\n".join(str(f) for f in self.files)
        test_files = "\n\n".join(str(f) for f in self.test_files)
        deleted_files = "\n".join(self.deleted_files)
        return (
            f"{self.git_branch}\n"
            f"{self.title}\n"
            f"{self.description}\n\n"
            f"{new_files}\n\n"
            f"{test_files}\n\n"
            f"{deleted_files}\n\n"
        )


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": Action.WRITE_PR,
            "description": "Writes a Pull Request",
            "parameters": WritePRParams.schema(),
        },
    },
]


SYSTEM_PROMPT = """You are a helpful AI assistant that writes code and creates Pull Requests.
You are an expert with Python and FastAPI.

### You are working on the following codebase

{codebase}

### Requirements

1. Follow the PEP 8 style guide.
2. Use the best Python and FastAPI cpractices.
3. Use the FastAPI best practices to organize your files
4. You must only create 1 PR at a time. If there is something to be fixed, amend the existing PR.
5. Include unit tests for every change you make. Use mocked data."""


USER_PROMPT = """Write a PR for this ticket:

{ticket}"""


def write_pr(
    ticket: Issue,
    conversation: Conversation,
    repo_files: List[Optional[GithubFile]],
    # code_suggestion: str,
):
    next = llm.stream_next(
        [
            {
                "role": "system",
                "content": SYSTEM_PROMPT.format(
                    codebase="\n".join(str(f) for f in repo_files)
                ),
            },
            {
                "role": "user",
                "content": USER_PROMPT.format(
                    ticket=ticket,
                    codebase="\n".join(str(f) for f in repo_files),
                    # suggestion=code_suggestion,
                ),
            },
        ]
        + conversation,
        tools=TOOLS,
    )
    return next
