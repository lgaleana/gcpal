from typing import Union

from agents.coder import WritePRParams
from agents.contributor import AmendPRParams
from ai import llm
from utils.state import Conversation


def sumamrize_test_failure(
    pr: Union[WritePRParams, AmendPRParams], failure_msg: str
) -> str:
    PROMPT = f"""I wrote the following Pull Request with unit tests, but the tests failed.
    Help me understand the error and fix the tests.

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


def summarize_architecture(conversation: Conversation) -> str:
    PROMPT = f"""Provide a summary of the software architecture."""

    summary = llm.stream_next(
        conversation
        + [
            {
                "role": "system",
                "content": PROMPT,
            }
        ]
    )
    assert isinstance(summary, str)
    return summary
