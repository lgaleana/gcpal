from typing import Union

from agents.coder import WritePRParams
from agents.contributor import AmendPRParams
from ai import llm


def sumamrize_test_failure(
    pr: Union[WritePRParams, AmendPRParams], failure_msg: str
) -> str:
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
