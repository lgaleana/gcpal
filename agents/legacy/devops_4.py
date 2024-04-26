from typing import List, Optional

from pydantic import BaseModel, Field

from ai import llm
from tools.github import GithubFile
from tools.jira import Issue
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

You can execute commands by calling the `execute_shell` function.
You are inside a docker container with ubuntu:latest.
You have access to Google Cloud Platform. You rely on a service key. You have Editor permissions.

You are working in the following project

### Project description

{project_description}

### Architecture overview

{project_architecture}

### The ticket assigned to you

{ticket}

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
    ticket: Issue,
    conversation: Conversation,
    project_description: str,
    project_architecture: str,
    repo: str,
    repo_files: List[Optional[GithubFile]],
    command_list: List[Command],
):
    next = llm.stream_next(
        [
            {
                "role": "system",
                "content": PROMPT.format(
                    project_description=project_description,
                    project_architecture=project_architecture,
                    ticket=ticket,
                    repo=repo,
                    codebase="\n".join(str(f) for f in repo_files),
                    commands="\n".join(
                        [f"# {c.command}\n{c.output_str()}" for c in command_list]
                    ),
                ),
            },
        ]
        + conversation,
        tools=TOOLS,
    )
    return next
