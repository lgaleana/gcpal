import json
import subprocess
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv()

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
                arguments=ai_action.payload.arguments.model_dump_json(),
            )
            command_list = "\n".join(ai_action.payload.arguments.commands)
            print_system("The following commands will be executed: ")
            print_system(f"```\n{command_list}\n```")
            user_message = user_input()
            if user_message == "y":
                process = execute_shell(ai_action.payload.arguments.commands)
                print_system()
                print_system(process.stdout)
                print_system(process.stderr)
                if process.returncode == 0:
                    conversation.add_tool_response(
                        tool_id=ai_action.payload.id,
                        message=f"Commands executed successfully. Stdout :: {process.stdout}",
                    )
                else:
                    conversation.add_tool_response(
                        tool_id=ai_action.payload.id,
                        message=f"There was an error executing the commands :: {process.stderr}",
                    )
            else:
                conversation.add_tool_response(
                    tool_id=ai_action.payload.id,
                    message=f"Commands not executed. Reason :: user feedback.",
                )
                conversation.add_user(user_message)

        if user_message == "persist":
            conversation.add_user("Please persist the conversation into disk.")
            conversation.add_system("Conversation persisted successfully.")
            print_system("Converstion to persist: ")
            print_system()
            print_system(json.dumps(conversation, indent=2))
            conversation.dump()
            break


def execute_shell(commands: List[str]) -> subprocess.CompletedProcess:
    # gcp_zone = os.getenv("GCP_ZONE")
    # gcp_project = os.getenv("GCP_PROJECT")
    # assert gcp_zone and gcp_project, "GCP info not found"
    commands = ["cd sandbox"] + commands
    commands_list = "\n".join(commands)
    return subprocess.run(
        # f"gcloud compute ssh --zone {gcp_zone} --project {gcp_project} -- command '{commands_list}'",
        commands_list,
        shell=True,
        executable="/bin/bash",
        capture_output=True,
        text=True,
    )


if __name__ == "__main__":
    conversation = Conversation.load()
    if conversation:
        conversation.add_system(
            (
                "Conversation loaded. Please resume the conversation where it was left."
                "Commands are only executed through the `execute_shell` tool."
            )
        )
    run(conversation)
