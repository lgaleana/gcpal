from typing import List, Optional, Union

from agents.coder import WritePRParams
from agents.contributor import AmendPRParams
from ai import llm
from tools.github import GithubFile
from utils.state import Conversation

from pydantic import BaseModel, Field


def sumamrize_test_failure(
    pr: Union[WritePRParams, AmendPRParams],
    failure_msg: str,
    repo_files: List[Optional[GithubFile]],
) -> str:
    codebase = "\n".join(str(f) for f in repo_files)

    PROMPT = f"""I wrote the following Pull Request with unit tests, but the tests failed.
    Help me understand the error and fix the tests.

    Codebase:
    {codebase}

    Pull request:
    {pr}

    Test failure message:
    ```
    {failure_msg}
    ```

    In one sentence, explain the error.
    Then, tell me how to fix the tests. Provide code changes. Tests must use mocked data.

    Error: ...
    Fix: ..."""

    summary = llm.stream_next(
        [
            {
                "role": "user",
                "content": PROMPT,
            }
        ]
    )
    assert isinstance(summary, str)
    return summary


def there_is_followup(text: str) -> bool:
    PROMPT = f"""Does the following text explicitly say that there is a followup action?
    {text}
    
    yes/no"""

    yes_no = llm.stream_next(
        [
            {
                "role": "user",
                "content": PROMPT,
            }
        ]
    )
    assert isinstance(yes_no, str)
    return "yes" in yes_no.lower()


class SummaryParams(BaseModel):
    project_description: str = Field(description="Brief description of the project.")
    architecture_overview: str = Field(
        description="Overview of the system architecture."
    )


def summarize_architecture(conversation: Conversation) -> SummaryParams:
    TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "summarize",
                "description": "Summarizes the project.",
                "parameters": SummaryParams.schema(),
            },
        },
    ]

    PROMPT = f"""Provide a brief description of the project and an overview of the system architecture."""

    summary = llm.stream_next(
        conversation
        + [
            {
                "role": "system",
                "content": PROMPT,
            }
        ],
        tools=TOOLS,
    )
    assert isinstance(summary, llm.RawTool)
    return SummaryParams.model_validate(summary.arguments)
