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

FastAPI application that lets users manage an inventory.

### Architecture overview

The software architecture for this FastAPI application will be a simple monolithic architecture, as it's a straightforward inventory management system. Here's a brief overview:

1. **FastAPI Application**: FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.6+ based on standard Python type hints. It will be used to handle all the HTTP requests and responses.
2. **Endpoints**: The application will have several endpoints to handle adding, updating, deleting, and viewing items in the inventory.
3. **Item Model**: This is the data model that will define the structure of the items in the inventory. It will include fields such as name, description, quantity, etc.
4. **Database**: The application will need a database to store the inventory data. You can choose any SQL or NoSQL database based on your preference and requirements.
5. **Server**: The application will be hosted on a server. You can choose to host it on a cloud provider like AWS, Google Cloud, or Azure, or on a local server.

This is a high-level overview of the architecture. The actual implementation details might vary based on your specific requirements and preferences.

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

### Instructions

1. Discuss the implementation with me. Omit code.
2. Only once I agree, create the PR.
"""


def next_action(
    ticket: Issue,
    conversation: Conversation,
    repo_files: List[Optional[GithubFile]],
):
    next = llm.stream_next(
        [
            {
                "role": "user",
                "content": PROMPT.format(
                    ticket=ticket,
                    codebase="\n".join(str(f) for f in repo_files),
                ),
            }
        ]
        + conversation,
        tools=TOOLS,
    )
    return next
