from typing import List, Union

from pydantic import BaseModel, Field

from ai import llm
from utils.io import print_system
from utils.state import Command, Conversation


class Action:
    CHAT = "chat"
    EXECUTE_SHELL = "execute_shell"


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


class Tool(llm.RawTool):
    arguments: ExecuteShellParams


class NextAction(BaseModel):
    name: str
    payload: Union[str, Tool]


PROMPT = """You are a helpful AI assistant that helps software engineers build software, using the best software engineering practices.

You can execute commands by calling the `execute_shell` function. You are inside an Ubuntu docker container.

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
    return NextAction(
        name=Action.EXECUTE_SHELL,
        payload=Tool(
            id=next.id,
            name=next.name,
            arguments=ExecuteShellParams.parse_obj(next.arguments),
        ),
    )
