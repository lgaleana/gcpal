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


PROMPT = """You are a helpful AI assistant that helps software engineers with devops tickets.

You are inside a docker container running ubuntu.
You have access to Google Cloud Platform. You are using the service account gcpal-881, that has the role Editor.

### Codebase

**Repository**: https://github.com/lgaleana/{repo}

{codebase}

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

### Commands that you have ran so far

{commands}

### Instructions

- The user doesn't have the ability to execute commands.
- You should always execute commands yourself instead of asking the user to do something for you.
- If the command has the flags, run it in a non-interactive way. Otherwise, it might time out."""


def next_action(
    conversation: Conversation,
    repo: str,
    repo_files: List[Optional[GithubFile]],
    command_list: List[Command],
):
    next = llm.stream_next(
        [
            {
                "role": "system",
                "content": PROMPT.format(
                    repo=repo,
                    codebase="\n".join(str(f) for f in repo_files),
                    commands="\n".join(
                        [f"# {c.command}\n{c.output_str()}" for c in command_list]
                    ),
                ),
            },
            {
                "role": "user",
                "content": "Hi",
            },
        ]
        + conversation,
        tools=TOOLS,
    )
    return next
