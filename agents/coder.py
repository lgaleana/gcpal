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


PROMPT = """You are a helpful AI assistant that writes code and creates Pull Requests.

You are working in the following project

### Project description

{project_description}

### Architecture overview

{project_architecture}

### The ticket assigned to you

{ticket}

### Codebase

{codebase}

### Requirements

1. Follow the best software engineering practices.
2. Consider the existing codebase.
3. Follow the best practices to organize your file structure.
4. Remember to add a new line at the end of each file.
5. Use absolute imports.
6. Include unit tests for every change you make. Use mocked data.
"""


def next_action(
    ticket: Issue,
    conversation: Conversation,
    project_description: str,
    project_architecture: str,
    repo_files: List[Optional[GithubFile]],
):
    next = llm.stream_next(
        [
            {
                "role": "user",
                "content": PROMPT.format(
                    project_description=project_description,
                    project_architecture=project_architecture,
                    ticket=ticket,
                    codebase="\n".join(str(f) for f in repo_files),
                ),
            }
        ]
        + conversation,
        tools=TOOLS,
    )
    return next
