import json
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from ai import llm
from utils.io import print_system


class ExecuteShelParams(BaseModel):
    commands: List[str] = Field(description="List of shell commands to execute")


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "execute_shell",
            "description": "Executes shell commands in MacOS",
            "parameters": ExecuteShelParams.schema(),
        },
    }
]


class NextAction(BaseModel):
    message: Optional[str]
    tool: Optional[ExecuteShelParams]


PROMPT = """You are a helpful AI assistant that helps software engineers build software.

Say hi."""


def next_action(conversation: List[Dict[str, str]]) -> NextAction:
    message, arguments = llm.stream_next(
        [{"role": "system", "content": PROMPT}] + conversation,
        tools=TOOLS,
    )
    return NextAction(
        message=message,
        tool=ExecuteShelParams.parse_raw(arguments) if arguments else None,
    )
