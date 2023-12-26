import traceback
from typing import List, Union

from pydantic import BaseModel, Field, ValidationError

from ai import llm
from utils.conversation import Conversation
from utils.io import print_system


class Action:
    CHAT = "chat"
    EXECUTE_SHELL = "execute_shell"
    PERSIST_CONVERSATION = "persist_conversation"


class ExecuteShellParams(BaseModel):
    commands: List[str] = Field(description="List of shell commands to execute")


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": Action.EXECUTE_SHELL,
            "description": "Executes shell commands in MacOS",
            "parameters": ExecuteShellParams.schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": Action.PERSIST_CONVERSATION,
            "description": "Persist the whole conversation history",
            "parameters": None,
        },
    },
]


class Tool(llm.RawTool):
    arguments: Union[ExecuteShellParams, None]


class NextAction(BaseModel):
    name: str
    payload: Union[str, Tool]


PROMPT = """You are a helpful AI assistant that helps software engineers build software, using the best software engineering practices.

Your build environment is a Google Cloud Compute Engine VM.
You can execute shell commands inside the VM.
All shell commands will be executed from within the home directory.

Say hi."""


def next_action(conversation: Conversation) -> NextAction:
    print_system(conversation)
    ai_response = llm.stream_next(
        [{"role": "system", "content": PROMPT}] + conversation,
        tools=TOOLS,
    )
    try:
        return _parse_ai_response(ai_response)
    except ValidationError as e:
        print_system(e)
        print_system(traceback.format_tb(e.__traceback__))
        ai_response = llm.stream_next(
            Conversation(
                conversation
                + [
                    {
                        "role": "system",
                        "content": (
                            f"Error parsing function parameters :: {e}\n"
                            f"Got :: {ai_response.arguments}\n"  # type: ignore
                            "Please fix the error."
                        ),
                    }
                ]
            ),
            tools=TOOLS,
        )
        return _parse_ai_response(ai_response)


def _parse_ai_response(next: Union[str, llm.RawTool]) -> NextAction:
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
        name=Action.PERSIST_CONVERSATION,
        payload=Tool(
            id=next.id,
            name=next.name,
            arguments=None,
        ),
    )
