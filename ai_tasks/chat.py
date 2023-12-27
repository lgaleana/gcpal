import traceback
from typing import List, Union

from pydantic import BaseModel, Field, ValidationError

from ai import llm
from utils.conversation import Conversation
from utils.io import print_system


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
            "description": "Executes shell commands for MacOS",
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

Every set of shell commands that you execute will begin from the home directory.
For example, if you execute `["mkdir foo", "cd foo"]`, the next command you execute won't be execute inside `foo/`.

Say hi."""


def next_action(conversation: Conversation) -> NextAction:
    print_system(conversation)
    next = llm.stream_next(
        [{"role": "system", "content": PROMPT}] + conversation,
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
