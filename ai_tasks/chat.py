from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from ai import llm


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
    tool_id: Optional[str]
    tool: Optional[ExecuteShelParams]


PROMPT = """You are a helpful AI assistant that helps software engineers build software.

Say hi."""


def next_action(conversation: List[Dict[str, str]]) -> NextAction:
    print(conversation)
    message, tool = llm.stream_next(
        [{"role": "system", "content": PROMPT}] + conversation,
        tools=TOOLS,
    )
    return NextAction(
        message=message,
        tool_id=tool.id if tool else None,
        tool=ExecuteShelParams.parse_obj(tool.arguments) if tool else None,
    )
