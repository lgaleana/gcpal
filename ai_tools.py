from typing import List, Optional

from pydantic import BaseModel, Field

from agents.coder import WritePRParams
from ai import llm
from utils.state import Conversation


def sumamrize_test_failure(pr: WritePRParams, failure_msg: str) -> str:
    PROMPT = """You are a helpful AI assistant that helps understand why the tests in a Pull Request have failed.

    Pull request:
    ```
    {pr}
    ```

    Test failure message:
    ```
    {failure_msg}
    ```

    In one sentence, explain why the tests failed.
    Next, provide the code changes to fix them. Tests must use mocked data.

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
