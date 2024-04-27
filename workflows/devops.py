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


def run(state: State, repo: str) -> None:
    codebase = github.get_repo_files(repo=repo)
    startup_commands = [
        f"cd /home/{repo}",
        "source venv/bin/activate",
        "git checkout main",
        "git pull origin main --rebase",
        "gcloud config set project gcpal-409321",
        "pwd",
    ]
    docker = DockerRunner()
    docker.adhoc_commands = startup_commands
    init_commands = docker.execute(startup_commands)
    codebase = github.get_repo_files(repo)

    conversation = state.conversation

    while True:
        ai_action = devops.next_action(
            conversation=conversation,
            repo=repo,
            repo_files=codebase,
            command_list=init_commands,
        )
        if isinstance(ai_action, str):
            conversation.add_assistant(ai_action)
            user_message = user_input()
            conversation.add_user(user_message)
        else:
            tools = [
                devops.ExecuteShellParams.model_validate(a) for a in ai_action.arguments
            ]
            conversation.add_tool(tool=ai_action)

            commands = [c for t in tools for c in t.commands]
            print_system("\n".join(commands))
            user_message = user_input()
            if user_message != "y":
                conversation.add_tool_response(
                    tool_id=ai_action.id,
                    message=f"Commands not executed. Reason: user feedback :: {user_message}",
                )
                continue

            commands = docker.execute(commands)

            last_command = commands[-1]
            output_str = "\n".join([c.output_str() for c in commands])
            if last_command.status == CommandStatus.ERROR:
                conversation.add_tool_response(
                    tool_id=ai_action.id,
                    message=f"ERROR :: {output_str}",
                )
            else:
                output_str = "\n".join(
                    [
                        c.output_str()
                        if c.command.startswith("cat")
                        or c.command == c.command.startswith("ls")
                        else c.output_str(max_len=2000)
                        for c in commands
                    ]
                )
                if last_command.status == CommandStatus.SUCCESS:
                    conversation.add_tool_response(
                        tool_id=ai_action.id,
                        message=output_str,
                    )
                else:
                    conversation.add_tool_response(
                        tool_id=ai_action.id,
                        message=f"{output_str}\n\nERROR: Command timed out...\n",
                    )
                    conversation.add_system(f"# cd /home/{repo}\n# pwd\n/home/{repo}")
                    conversation.add_user(
                        "Verify if the command executed successfully."
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

    run(state, repo=args.repo)
