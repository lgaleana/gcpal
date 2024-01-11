from pydantic import BaseModel
from typing import Any, Dict, List, Literal, Optional

from utils.io import print_system


class Conversation(List[Dict[str, Any]]):
    def __init__(self, iterable: List[Dict[str, Any]] = []):
        super().__init__(iterable)

    def add_assistant(self, message: str) -> None:
        self.append({"role": "assistant", "content": message})

    def add_system(self, message: str) -> None:
        self.append({"role": "system", "content": message})

    def add_user(self, message: str) -> None:
        self.append({"role": "user", "content": message})

    def add_tool(self, tool_id: str, arguments: Optional[str]) -> None:
        self.append(
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": tool_id,
                        "type": "function",
                        "function": {
                            "name": "execute_shell",
                            "arguments": arguments,
                        },
                    }
                ],
                "content": None,
            }
        )

    def add_tool_response(self, tool_id: str, message: str) -> None:
        self.append({"role": "tool", "content": message, "tool_call_id": tool_id})

    def empty(self) -> bool:
        return len(self) == 0


class CommandStatus:
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"


class Command(BaseModel):
    command: str
    output: List[str] = []
    status: Literal[
        CommandStatus.SUCCESS,  # type: ignore
        CommandStatus.ERROR,  # type: ignore
        CommandStatus.TIMEOUT,  # type: ignore
    ]

    def output_str(self) -> str:
        return "\n".join(self.output)


class State(BaseModel):
    name: str
    agent: str
    conversation: Conversation = Conversation()
    commands: List[Command] = []

    class Config:
        arbitrary_types_allowed = True

    @staticmethod
    def load() -> "State":
        from db.devops.state import payload

        conversation = Conversation(payload.pop("conversation", []))
        if not conversation.empty():
            conversation.add_system(
                "Conversation loaded. Say hi and continue the conversation where it was left."
            )
        return State(**payload, conversation=Conversation(conversation))

    def persist(self) -> None:
        payload_str = "payload = " + self.model_dump_json(indent=4)
        payload_str = payload_str.replace(": null\n", ": None\n")
        payload_str = payload_str.replace(": true\n", ": True\n")
        payload_str = payload_str.replace(": false\n", ": False\n")
        with open(f"db/{self.agent}/{self.name}.py", "w") as file:
            file.write(payload_str)
