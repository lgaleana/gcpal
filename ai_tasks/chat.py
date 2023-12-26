from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field

from ai import llm


class Action:
    CHAT = "chat"
    EXECUTE_SHELL = "execute_shell"
    PERSIST_CONVERSATION = "persist_conversation"


class ExecuteShelParams(BaseModel):
    commands: List[str] = Field(description="List of shell commands to execute")


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": Action.EXECUTE_SHELL,
            "description": "Executes shell commands in MacOS",
            "parameters": ExecuteShelParams.schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": Action.PERSIST_CONVERSATION,
            "description": "Persist the whole conversation history",
            "parameters": {},
        },
    },
]


class Tool(llm.RawTool):
    arguments: Union[ExecuteShelParams, None]


class NextAction(BaseModel):
    name: str
    payload: Union[str, Tool]


PROMPT = """You are a helpful AI assistant that helps software engineers build software.

Say hi."""


def next_action(conversation: List[Dict[str, str]]) -> NextAction:
    print(conversation)
    next = llm.stream_next(
        [{"role": "system", "content": PROMPT}] + conversation,
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
                arguments=ExecuteShelParams.parse_obj(next.arguments),
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
