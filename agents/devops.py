from typing import List, Optional

from pydantic import BaseModel, Field

from ai import llm
from tools.github import GithubFile
from utils.state import Command, Conversation


class Action:
    CHAT = "chat"
    EXECUTE_SHELL = "execute_shell"
    PR = "pr"


class ExecuteShellParams(BaseModel):
    commands: List[str] = Field(description="List of shell commands to execute")


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": Action.EXECUTE_SHELL,
            "description": "Executes shell commands in Ubuntu",
            "parameters": ExecuteShellParams.schema(),
        },
    },
]


PROMPT = """You are a helpful AI assistant that helps software engineers with devops tasks.

You can execute commands by calling the `execute_shell` function.
You are inside an Ubuntu docker container.
You have access to Google Cloud Platform. You rely on a service key. You have Editor permissions.

### Packages installed

```
python
pip
venv
curl
git
gcloud
docker
gh
```

### Codebase

**Github repo**: https://github.com/lgaleana/email-sequences
**Main branch**: `main`

{codebase}

### Commands that you have ran so far

{commands}

### Instructions

- The user doesn't have the ability to execute commands.
- You must always request the information that you need from them.
- You should always execute commands yourself instead of asking the user to do something for you.

Say hi."""


def next_action(
    conversation: Conversation,
    repo_files: List[Optional[GithubFile]],
    command_list: List[Command],
):
    next = llm.stream_next(
        [
            {
                "role": "system",
                "content": PROMPT.format(
                    codebase="\n".join(str(f) for f in repo_files),
                    commands="\n".join(
                        [f"# {c.command}\n{c.output_str()}" for c in command_list]
                    ),
                ),
            }
        ]
        + conversation,
        tools=TOOLS,
    )
    return next
