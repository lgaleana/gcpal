import subprocess

from ai_tasks import chat
from utils.io import user_input, print_system


def run() -> None:
    conversation = []
    while True:
        ai_action = chat.next_action(conversation)

        if not ai_action.tool:
            conversation.append({"role": "assistant", "content": ai_action.message})
            user_message = user_input()
            conversation.append({"role": "user", "content": user_message})
        else:
            conversation.append(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": ai_action.tool_id,
                            "type": "function",
                            "function": {
                                "name": "execute_shell",
                                "arguments": ai_action.tool.model_dump_json(),
                            },
                        }
                    ],
                }
            )
            command_list = "\n".join(ai_action.tool.commands)
            print_system("The following commands will be executed: ")
            print_system()
            print_system(command_list)
            user_message = user_input()
            if user_message == "y":
                execute_shell(command_list)
                conversation.append(
                    {
                        "role": "tool",
                        "content": "Commands executed successfully.",
                        "tool_call_id": ai_action.tool_id,
                    }
                )
            else:
                conversation.append(
                    {
                        "role": "tool",
                        "content": f"Commands not executed. Reason :: user feedback.",
                        "tool_call_id": ai_action.tool_id,
                    }
                )
                conversation.append({"role": "user", "content": user_message})


def execute_shell(command_list: str):
    command_list = "cd sandbox\n" + command_list
    x = subprocess.run(command_list, shell=True, executable="/bin/bash")
    print_system(str(x))


if __name__ == "__main__":
    run()
