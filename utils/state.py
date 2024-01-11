import json
from pydantic import BaseModel
from typing import Any, Dict, List, Literal, Optional


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
    def load(name: str, agent: str) -> "State":
        with open(f"db/{agent}/{name}.json", "r") as file:
            payload = json.load(file)

        return State(
            name=name,
            agent=agent,
            conversation=payload.conversation,
            commands=payload.commands,
        )

    def persist(self) -> None:
        with open(f"db/{self.agent}/{self.name}.json", "w") as file:
            json.dump(self.model_dump_json(), file, indent=4)
