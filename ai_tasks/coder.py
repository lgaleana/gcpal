from typing import List

from pydantic import BaseModel, Field

from ai import llm
from utils.state import Command, Conversation


class Action:
    COLLECT_INFORMATION = "collect_information"
    SHARE_PLAN = "share_plan"
    WRITE_PR = "write_pr"


class WritePR(BaseModel):
    pr_content: str = Field(description="What will be included in the PR?")


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": Action.WRITE_PR,
            "description": "Writes a Pull Request",
            "parameters": WritePR.schema(),
        },
    },
]


PROMPT = """You are a helpful AI assistant that builds features by writing code and creating Pull Requests.
You must use the best sofwtware engineering practices.

You must build features incrementally. A single feature can be composed by multiple PRs. The PRs that you write must follow the following criteria:
1. Have single concern or purpose. That is, they should implement one single functionality. Examples:
    - Write a method with a single functionality.
    - Write the first functionality of a method.
    - Add another functionality to an existing method.
    - Integrate a method into an existing method.
    - Fix a bug.
    - Write an integration test.
2. Be small. They sould be easy to review.
3. Include tests. Through the single-concern property, they should be easily tested.

To accomplish the above, it should be clear to you what are the set of PRs needed to build the feature.

Feature to build: {feature}.

You are working with an already existing codebase, so you must consider what has been built so far.

Directory structure:
```
{code}
```

Git history:
```
{git}
```

Python packages already installed:
```
{pip}
```"""


def next_action(feature: str, commands: List[Command], conversation: Conversation):
    next = llm.stream_next(
        [
            {
                "role": "user",
                "content": PROMPT.format(
                    feature=feature,
                    code=commands[0].output_str(),
                    git=commands[1].output_str(),
                    pip=commands[2].output_str(),
                ),
            }
        ]
        + conversation,
        tools=TOOLS,
    )
    return next
