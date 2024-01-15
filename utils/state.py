import json
from copy import deepcopy
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

    def copy(self) -> "Conversation":
        return deepcopy(self)

    def remove_last_failed_tool(self, fail_msg: str) -> "Conversation":
        new_conversation = self.copy()
        for i in range(len(new_conversation) - 1, 0, -1):
            if new_conversation[i]["content"] == fail_msg:
                del new_conversation[i - 2 : i + 1]
                break
        return new_conversation

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


command_list = []


class State(BaseModel):
    name: str
    agent: str
    conversation: Conversation = Conversation()

    class Config:
        arbitrary_types_allowed = True

    @staticmethod
    def load(name: str, agent: str) -> "State":
        with open(f"db/{agent}/{name}.json", "r") as file:
            payload = json.load(file)

        return State(
            name=name,
            agent=agent,
            conversation=Conversation(payload["conversation"]),
        )

    def persist(self) -> None:
        payload = self.model_dump()
        payload["commands"] = [c.json() for c in command_list]
        with open(f"db/{self.agent}/{self.name}.json", "w") as file:
            json.dump(payload, file, indent=4)
