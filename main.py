import json
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv()

from ai_tasks import chat
from utils import docker
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
            commands = ai_action.payload.arguments.commands
            command_list = "\n".join(commands)
            print_system("The following commands will be executed: ")
            print_system(f"```\n{command_list}\n```")

            user_message = user_input()
            if user_message == "y" or user_message == "ok" or user_message == "":
                outputs, errors = docker.execute(commands)

                stdout = str(outputs)
                max_len = len(commands) * 30
                if len(outputs) > max_len:
                    stdout = f"<long output>... {stdout[-max_len:]}"
                if not errors:
                    conversation.add_tool_response(
                        tool_id=ai_action.payload.id,
                        message=f"Commands executed successfully. Stdout :: {stdout}",
                    )
                else:
                    conversation.add_tool_response(
                        tool_id=ai_action.payload.id,
                        message=f"Some commands prodiced errors. Stdout :: {stdout}, stderr: {errors}",
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


if __name__ == "__main__":
    conversation = Conversation.load()
    if conversation:
        conversation.add_system(
            "Conversation loaded. Please resume the conversation where it was left."
        )
    run(conversation)
