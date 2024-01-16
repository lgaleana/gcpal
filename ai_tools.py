from typing import List, Optional

from pydantic import BaseModel, Field

from agents.coder import WritePRParams
from ai import llm
from utils.state import Conversation


def sumamrize_test_failure(pr: WritePRParams, failure_msg: str) -> str:
    PROMPT = """I wrote the following Pull Request with unit tests, but the tests failed.
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
                "content": PROMPT.format(pr=pr, failure_msg=failure_msg),
            }
        ]
    )
    assert isinstance(summary, str)
    return summary
