from typing import List, Union

from pydantic import BaseModel, Field

from ai import llm
from utils.io import print_system
from utils.state import Command, Conversation


class Action:
    CHAT = "chat"
    EXECUTE_SHELL = "execute_shell"
    PR = "pr"


class ExecuteShellParams(BaseModel):
    commands: List[str] = Field(description="List of shell commands to execute")


class WriteCodeParams(BaseModel):
    feature: str = Field(description="Feature to build through the Pull Request")


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": Action.EXECUTE_SHELL,
            "description": "Executes shell commands in Ubuntu",
            "parameters": ExecuteShellParams.schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": Action.PR,
            "description": "Delegates writing a Pull Requests to the coding assistant",
            "parameters": WriteCodeParams.schema(),
        },
    },
]


class Tool(llm.RawTool):
    arguments: Union[ExecuteShellParams, WriteCodeParams]


class NextAction(BaseModel):
    name: str
    payload: Union[str, Tool]


PROMPT = """You are a helpful AI assistant that helps software engineers build software, using the best software engineering practices.

You can execute commands by calling the `execute_shell` function.
You are inside an Ubuntu docker container.
The packages installed are:
- python
- pip
- venv
- curl
- git
- gcloud
- docker
- gh
You are here:
```
{commands}
```

The user doesn't have the ability to execute commands.
You must always request the information that you need from them.
You shoudl always execute commands yourself instead of asking the user to do something for you.

You work with another AI assistant, that is the best coder in the world.
The work between you an the coder assistant is split up in the following way:
- Story: This is a high-level goal in the eyes of the user. Example:
    - Build a web application.
    - Build the frontend.
    - Build the backend.
- Task: Something that needs to be done. Examples:
    - Implement a React component.
    - Implement API endppoints.
    - Set up the database.
- Subtask: Steps to accomplish the task. Examples:
    - Write a Pull Request.
    - Execute shell commands.
- Pull Request: A Pull Request is specific to writing code to build a feature and then pushing up that code for review. Examples:
    - Query the backend from your search React component.
    - Implement a method that fetches from the database.
    - Integrate the database with your search endpoint.
  All of these can be described as single-concern features. They can easily be tested with unit tests.

The coding assistant can only work with Pull Requests. When the user is ready to build a coding feature, you must delegate that task to the coding assitant. The coding assistant will branch off, write the feature and push it for review.

Say hi."""


def next_action(conversation: Conversation, command_list: List[Command]) -> NextAction:
    print_system(conversation)

    commands_str = "\n".join([f"# {c.command}\n{c.output_str()}" for c in command_list])
    next = llm.stream_next(
        [{"role": "system", "content": PROMPT.format(commands=commands_str)}]
        + conversation,
        tools=TOOLS,
    )

    if isinstance(next, str):
        return NextAction(name=Action.CHAT, payload=next)
    if next.name == Action.EXECUTE_SHELL:
        return NextAction(
            name=Action.EXECUTE_SHELL,
            payload=Tool(
                id=next.id,
                name=next.name,
                arguments=ExecuteShellParams.parse_obj(next.arguments),
            ),
        )
    return NextAction(
        name=Action.PR,
        payload=Tool(
            id=next.id,
            name=next.name,
            arguments=WriteCodeParams.parse_obj(next.arguments),
        ),
    )
