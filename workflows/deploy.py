import argparse
import time

from dotenv import load_dotenv

load_dotenv()

from agents import devops
from tools import github
from tools.docker.commands import DockerRunner
from utils.io import user_input, print_system
from utils.state import CommandStatus, Conversation, State


AGENT = "devops"

TOOL_FAIL_MSG = "Fix the tests and re-create the PR. Go ahead."


def run(state: State, repo: str) -> None:
    startup_commands = [
        f"cd /home/{repo}",
        "source venv/bin/activate",
        "git checkout main",
        "git pull origin main --rebase",
        "gcloud config set project gcpal-409321",
        "pwd",
    ]
    docker = DockerRunner(startup_commands)
    init_commands = docker.execute(startup_commands)
    codebase = github.get_repo_files(repo)

    conversation = state.conversation

    while True:
        ai_action = devops.next_action(
            conversation, repo=repo, repo_files=codebase, command_list=init_commands
        )
        if isinstance(ai_action, str):
            conversation.add_assistant(ai_action)
            user_message = user_input()
            conversation.add_user(user_message)
        else:
            tool = devops.ExecuteShellParams.model_validate(ai_action.arguments)
            conversation.add_tool(tool=ai_action)

            print_system("\n".join(tool.commands))
            user_message = user_input()
            if user_message != "y":
                conversation.add_tool_response(
                    tool_id=ai_action.id,
                    message=f"Commands not executed. Reason: user feedback :: {user_message}",
                )
                continue

            commands = docker.execute(tool.commands)

            last_command = commands[-1]
            output_str = "\n".join([c.output_str() for c in commands])
            if last_command.status == CommandStatus.ERROR or "ERROR: " in output_str:
                conversation.add_tool_response(
                    tool_id=ai_action.id,
                    message=f"ERROR :: {output_str}",
                )
            else:
                max_len = 500
                if len(output_str) > max_len:
                    output_str = f"Output too long: ... {output_str[-max_len:]}"
                if last_command.status == CommandStatus.SUCCESS:
                    conversation.add_tool_response(
                        tool_id=ai_action.id,
                        message=output_str,
                    )
                else:
                    conversation.add_tool_response(
                        tool_id=ai_action.id,
                        message=f"{output_str}\n\nERROR: Command timed out...",
                    )
        state.persist()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", type=str)
    parser.add_argument("--name", type=str, default=None)
    args = parser.parse_args()

    states_dir = f"db/{AGENT}/"
    if args.name:
        state = State.load(args.name, AGENT)
    else:
        state = State(
            name=str(time.time()), agent=AGENT, conversation=Conversation(), pr=None
        )

    run(state, args.repo)
