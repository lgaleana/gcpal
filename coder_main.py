import json
import time

from dotenv import load_dotenv

load_dotenv()

from ai_tasks import coder
from utils import github
from utils import jira
from utils.files import create_files, DIFFS_DIR
from utils.docker import commands as docker, container
from utils.io import user_input, print_system
from utils.state import CommandStatus, Conversation


def run() -> None:
    conversation = Conversation()
    tickets = jira.get_grouped_issues()
    codebase = github.get_repo_files()
    git_history = github.get_last_commits(n=10)
    active_ticket = jira.find_issue(tickets, "SBX-50")
    assert active_ticket
    docker.startup()
    docker.execute(["cd /home/app", "pwd", "source venv/bin/activate"])
    session = str(time.time())

    while True:
        ai_action = coder.next_action(
            active_ticket, conversation, tickets, codebase, git_history
        )
        if isinstance(ai_action, str):
            conversation.add_assistant(ai_action)
            user_message = user_input()
            conversation.add_user(user_message)
        else:
            tool = coder.WritePRParams.parse_obj(ai_action.arguments)
            print_system(tool)
            conversation.add_tool(
                tool_id=ai_action.id, arguments=json.dumps(ai_action.arguments)
            )
            user_message = user_input()
            if user_message != "y":
                conversation.add_tool_response(
                    tool_id=ai_action.id,
                    message=f"Didn't execute. Reason: user feedback :: {user_message}",
                )
                continue

            # Create files locally first
            print_system("Copying files to container...")
            root_path = f"{DIFFS_DIR}/{session}"
            create_files(tool.new_files + tool.test_files, root_path=root_path)

            try:
                # 1. Copy them to docker container
                container.copy_files(
                    files=tool.new_files + tool.test_files,
                    root=root_path,
                    container_path=f"/home/app",
                )
                docker.execute_one("git diff")

                # 2. Install new requirements
                pip = docker.execute_one("python3 -m pip install -r requirements.txt")
                if pip.status == CommandStatus.ERROR:
                    conversation = _rollback(
                        conversation,
                        ai_action.id,
                        f"running :: `{pip.command}`. Error :: {pip.output_str()}",
                    )
                    continue

                # 3. Run tests
                pytest = docker.execute_one("python3 -m pytest")
                if (
                    pytest.status == CommandStatus.ERROR
                    or "= ERRORS =" in pytest.output_str()
                ):
                    conversation = _rollback(
                        conversation,
                        ai_action.id,
                        f"running :: `{pytest.command}`. Error :: {pytest.output_str()}",
                    )
                    continue

                # 4. Create commit

                # 5. Push to github
            except Exception as e:
                conversation = _rollback(
                    conversation,
                    ai_action.id,
                    str(e),
                )
                continue

            conversation.add_tool_response(
                tool_id=ai_action.id,
                message=(
                    f"`{pip.command}` succeeded\n"
                    f"`{pytest.command}` succeeded\n"
                    "PR created successfully"
                ),
            )
            print_system("Success.")
            user_message = user_input()


if __name__ == "__main__":
    run()


def _rollback(conversation: Conversation, tool_id: str, agent_msg: str) -> Conversation:
    print_system("Rolling back...")
    docker.execute(
        [
            "cd /home/app",
            "pwd",
            "source venv/bin/activate",
            "git restore .",  # roll back files
            "git clean -fd",  # roll back files
            "python3 -m pip uninstall -r requirements.txt -y",  # roll back packages
            "python3 -m pip install -r requirements.txt",
        ]
    )
    conversation.add_tool_response(
        tool_id=tool_id,
        message=f"Error :: {agent_msg}",
    )
    return conversation
