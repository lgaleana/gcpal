import argparse
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv()

from ai_tasks import chat
from utils import docker
from utils.io import user_input, print_system
from utils.state import Conversation, state, State


def run(_conversation: List[Dict[str, Any]] = []) -> None:
    if _conversation:
        state.conversation = Conversation(_conversation)
    conversation = state.conversation
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
                        message=f"Commands executed. Stdout :: {stdout}",
                    )
                else:
                    conversation.add_tool_response(
                        tool_id=ai_action.payload.id,
                        message=f"Commands produced an error. Stdout :: {stdout}, stderr: {errors}",
                    )
            else:
                conversation.add_tool_response(
                    tool_id=ai_action.payload.id,
                    message=f"Commands not executed. Reason :: user feedback.",
                )
                if user_message != "persist":
                    conversation.add_user(user_message)

        if user_message == "persist":
            conversation.add_user("Please persist the conversation into disk.")
            conversation.add_system("Conversation persisted successfully.")
            state.persist()
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--new", action="store_true")
    args = parser.parse_args()
    if args.new:
        state = State()
    run()
