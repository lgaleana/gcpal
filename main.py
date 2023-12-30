import argparse
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv

load_dotenv()

from ai_tasks import chat
from utils import docker
from utils.io import user_input, print_system
from utils.state import Command, CommandStatus, Conversation, state, State


def run(_conversation: List[Dict[str, Any]] = []) -> None:
    if _conversation:
        state.conversation = Conversation(_conversation)
    conversation = state.conversation

    initial_commands = docker.adhoc()

    while True:
        ai_action = chat.next_action(conversation, initial_commands)

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
            if isinstance(ai_action.payload.arguments, chat.ExecuteShellParams):
                commands = ai_action.payload.arguments.commands
                command_list = "\n".join(commands)
                print_system("The following commands will be executed: ")
                print_system(f"```\n{command_list}\n```")

                user_message = user_input()
                if user_message == "y" or user_message == "ok" or user_message == "":
                    executed_commands = docker.execute(commands)
                    stdout, stderr = _process_outputs(executed_commands)
                    if not stderr:
                        conversation.add_tool_response(
                            tool_id=ai_action.payload.id,
                            message=f"Commands executed. Stdout :: {stdout}",
                        )
                    else:
                        conversation.add_tool_response(
                            tool_id=ai_action.payload.id,
                            message=f"Commands produced errors. Stdout :: {stdout}, stderr: {stderr}",
                        )
                else:
                    conversation.add_tool_response(
                        tool_id=ai_action.payload.id,
                        message=f"Commands not executed. Reason :: user feedback.",
                    )
                    conversation.add_user(user_message)
            else:
                print_system(f"Code: {ai_action.payload.arguments.feature}")
                user_message = user_input()

        if user_message == "persist":
            conversation.add_user("Please persist the conversation into disk.")
            conversation.add_system("Conversation persisted successfully.")
            state.persist()
            break


def _process_outputs(executed_commands: List[Command]) -> Tuple[List[str], List[str]]:
    MAX_LEN = 100

    stdout = []
    stderr = []
    for command in executed_commands:
        if command.status == CommandStatus.TIMEOUT:
            stderr.append(
                f"Process is hanging after {docker.TIMEOUT}s. Connection restarted."
            )
            return stdout, stderr

        output_str = command.output_str()
        if command.status == CommandStatus.SUCCESS:
            if len(output_str) >= MAX_LEN:
                stdout.append(output_str[-MAX_LEN:])
            else:
                stdout.append(output_str)
        else:
            stderr.append(output_str)

    return stdout, stderr


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--new", action="store_true")
    args = parser.parse_args()
    if args.new:
        state = State()

    docker.startup()

    run()
