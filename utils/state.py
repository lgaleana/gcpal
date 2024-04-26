import json
from copy import deepcopy
from pydantic import BaseModel
from typing import Any, Dict, List, Literal, Optional

from ai.llm import RawTool
from tools.github import PullRequest


class Conversation(List[Dict[str, Any]]):
    def __init__(self, iterable: List[Dict[str, Any]] = []):
        super().__init__(iterable)

    def add_assistant(self, message: str) -> None:
        self.append({"role": "assistant", "content": message})

    def add_system(self, message: str) -> None:
        self.append({"role": "system", "content": message})

    def add_user(self, message: str) -> None:
        self.append({"role": "user", "content": message})

    def add_tool(self, tool: RawTool) -> None:
        self.append(
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": tool.id,
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "arguments": json.dumps(tool.arguments, indent=2),
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

    def remove_last_failed_tool(self, fail_msg: str) -> None:
        for i in range(len(self) - 1, 0, -1):
            if self[i]["content"] == fail_msg:
                del self[i - 2 : i + 1]
                break

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

    def output_str(self, max_len: int = -1) -> str:
        output_str = "\n".join(self.output)
        if max_len >= 0:
            output_str = f"Output too long: ... {output_str[-max_len:]}"
        return output_str


command_list = []


class State(BaseModel):
    name: str
    agent: str
    conversation: Conversation = Conversation()
    pr: Optional[PullRequest] = None
    project_description: Optional[str] = None
    project_architecture: Optional[str] = None
    acted_comments: List = []

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
            pr=payload.get("pr"),
            project_description=payload.get("project_description"),
            project_architecture=payload.get("project_architecture"),
            acted_comments=payload.get("acted_comments", []),
        )

    def _persist(self, name: str) -> None:
        payload = self.model_dump()
        payload["commands"] = [c.json() for c in command_list]
        with open(f"db/{self.agent}/{name}.json", "w") as file:
            json.dump(payload, file, indent=4)

    def persist(self) -> None:
        self._persist(self.name)

    def final_persist(self, final_name: str) -> None:
        self._persist(final_name)
