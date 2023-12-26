import json
import subprocess
from typing import Any, Dict, List

from ai_tasks import chat
from utils.conversation import Conversation
from utils.io import user_input, print_system


def run(_conversation: List[Dict[str, Any]] = []) -> None:
    conversation = Conversation(_conversation)
    while True:
        ai_action = chat.next_action(conversation)

        if ai_action.name == chat.Action.CHAT and isinstance(ai_action.payload, str):
            conversation.add_assistant(ai_action.payload)
            user_message = user_input()
            conversation.add_user(user_message)
        else:
            assert isinstance(ai_action.payload, chat.Tool)
            conversation.add_tool(
                tool_id=ai_action.payload.id,
                arguments=ai_action.payload.model_dump_json(),
            )
            if ai_action.name == chat.Action.EXECUTE_SHELL:
                assert ai_action.payload.arguments
                command_list = "\n".join(ai_action.payload.arguments.commands)
                print_system("The following commands will be executed: ")
                print_system()
                print_system(command_list)
                user_message = user_input()
                if user_message == "y":
                    completed = execute_shell(command_list)
                    if completed.returncode == 0:
                        conversation.add_tool_response(
                            tool_id=ai_action.payload.id,
                            message="Commands executed successfully.",
                        )
                    else:
                        conversation.add_tool_response(
                            tool_id=ai_action.payload.id,
                            message=f"There was an error executing the commands :: {completed.stderr}",
                        )
                else:
                    conversation.add_tool_response(
                        tool_id=ai_action.payload.id,
                        message=f"Commands not executed. Reason :: user feedback.",
                    )
                    conversation.add_user(user_message)
            else:
                print_system("Converstion to persist: ")
                print_system()
                print_system(json.dumps(conversation, indent=2))
                break


def execute_shell(command_list: str) -> subprocess.CompletedProcess:
    command_list = "cd sandbox\n" + command_list
    return subprocess.run(command_list, shell=True, executable="/bin/bash")


if __name__ == "__main__":
    run()
