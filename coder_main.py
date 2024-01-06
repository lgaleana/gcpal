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


def _rollback(
    conversation: Conversation, tool_id: str, branch: str, agent_msg: str
) -> Conversation:
    print_system()
    print_system("!!!!! Rolling back...")
    docker.execute(
        [
            "cd /home/app",
            "pwd",
            "source venv/bin/activate",
            "python3 -m pip uninstall -r requirements.txt -y",  # roll back packages
            "python3 -m pip install -r requirements.txt",
            "git restore .",  # roll back files
            "git clean -fd",  # roll back files
            "git checkout main",
            f"git branch -D {branch}",  # roll back branch
            f"git push origin --delete {branch}",  # rollb back github branch
        ]
    )
    print_system("Rollback successful...")
    conversation.add_tool_response(
        tool_id=tool_id,
        message=f"Error :: {agent_msg}",
    )
    return conversation


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
            tool = coder.WritePRParams.model_validate(ai_action.arguments)
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
            create_files(tool.files + tool.test_files, root_path=root_path)

            try:
                # 1. Create a new branch and checkout
                branch = docker.execute_one(f"git checkout -b {tool.git_branch}")
                if (
                    branch.status == CommandStatus.ERROR
                    or "fatal:" in branch.output_str()
                ):
                    conversation = _rollback(
                        conversation,
                        ai_action.id,
                        tool.git_branch,
                        f"running :: `{branch.command}`. Error :: {branch.output_str()}",
                    )
                    continue

                # 2. Copy files to docker container
                container.copy_files(
                    files=tool.files + tool.test_files,
                    root=root_path,
                    container_path=f"/home/app",
                )
                docker.execute_one("git status")

                # 3. Install new requirements
                pip = docker.execute_one("python3 -m pip install -r requirements.txt")
                if pip.status == CommandStatus.ERROR:
                    conversation = _rollback(
                        conversation,
                        ai_action.id,
                        tool.git_branch,
                        f"running :: `{pip.command}`. Error :: {pip.output_str()}",
                    )
                    continue

                # 4. Run tests
                pytest = docker.execute_one("python3 -m pytest")
                if (
                    pytest.status == CommandStatus.ERROR
                    or "= ERRORS =" in pytest.output_str()
                    or "= FAILURES =" in pytest.output_str()
                ):
                    conversation = _rollback(
                        conversation,
                        ai_action.id,
                        tool.git_branch,
                        f"running :: `{pytest.command}`. Error :: {pytest.output_str()}",
                    )
                    conversation.add_user(
                        "Your tests had errors. Fix them and re-create the PR. Go."
                    )
                    continue

                # 5. Create commit and push
                commit_commands = docker.execute(
                    [
                        "git add .",
                        f'git commit -m "{tool.title}"',
                        f"git push origin {tool.git_branch}",
                    ]
                )
                for c in commit_commands:
                    if c.status == CommandStatus.ERROR:
                        conversation = _rollback(
                            conversation,
                            ai_action.id,
                            tool.git_branch,
                            f"running :: `{c.command}`. Error :: {c.output_str()}",
                        )
                        continue

                # 5. Create PR
                pr_url = github.create_pr(
                    head=tool.git_branch,
                    base="main",
                    title=tool.title,
                    description=tool.description,
                    test_plan="pytest",
                )
            except Exception as e:
                print_system(f"!!!!! ERROR: {e}")
                conversation = _rollback(
                    conversation,
                    ai_action.id,
                    tool.git_branch,
                    str(e),
                )
                continue

            conversation.add_tool_response(
                tool_id=ai_action.id,
                message=(f"PR created successfully :: {pr_url}"),
            )
            print_system(pr_url)
            user_message = user_input()


if __name__ == "__main__":
    run()
