import subprocess

from ai_tasks import chat
from utils.conversation import Conversation
from utils.io import user_input, print_system


def run() -> None:
    conversation = Conversation()
    while True:
        ai_action = chat.next_action(conversation)

        if not ai_action.tool and ai_action.message:
            conversation.add_assistant(ai_action.message)
            user_message = user_input()
            conversation.add_user(user_message)
        elif ai_action.tool and ai_action.tool_id:
            conversation.add_tool(
                tool_id=ai_action.tool_id, arguments=ai_action.tool.model_dump_json()
            )
            command_list = "\n".join(ai_action.tool.commands)
            print_system("The following commands will be executed: ")
            print_system()
            print_system(command_list)
            user_message = user_input()
            if user_message == "y":
                completed = execute_shell(command_list)
                if completed.returncode == 0:
                    conversation.add_tool_response(
                        tool_id=ai_action.tool_id,
                        message="Commands executed successfully.",
                    )
                else:
                    conversation.add_tool_response(
                        tool_id=ai_action.tool_id,
                        message=f"There was an error executing the commands :: {completed.stderr}",
                    )
            else:
                conversation.add_tool_response(
                    tool_id=ai_action.tool_id,
                    message=f"Commands not executed. Reason :: user feedback.",
                )
                conversation.add_user(user_message)
        else:
            raise AssertionError("Invalid input.")


def execute_shell(command_list: str) -> subprocess.CompletedProcess:
    command_list = "cd sandbox\n" + command_list
    return subprocess.run(command_list, shell=True, executable="/bin/bash")


if __name__ == "__main__":
    run()
