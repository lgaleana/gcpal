import json

from typing import Any, Dict, List, Optional


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

    @staticmethod
    def load() -> "Conversation":
        from db.conversation import payload

        return Conversation(payload)

    def dump(self) -> None:
        payload_str = "payload = " + json.dumps(self, indent=4)
        payload_str = payload_str.replace(": null\n", ": None\n")
        with open("db/conversation.py", "w") as file:
            file.write(payload_str)
