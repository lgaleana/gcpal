import argparse
import time

from dotenv import load_dotenv

load_dotenv()

from agents import devops
from tools import github
from tools import jira
from tools.docker.commands import DockerRunner
from utils.io import user_input, print_system
from utils.state import CommandStatus, Conversation, State
from workflows.plan_project import AGENT as PM_AGENT


AGENT = "devops"


def run(context_state: State, state: State, repo: str, ticket_key: str) -> None:
    assert context_state.project_description
    assert context_state.project_architecture

    tickets = jira.get_grouped_issues(ticket_key.split("-")[0])
    codebase = github.get_repo_files(repo=repo)
    active_ticket = jira.find_issue(tickets, ticket_key)
    assert active_ticket
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
            ticket=active_ticket,
            conversation=conversation,
            project_description=context_state.project_description,
            project_architecture=context_state.project_architecture,
            repo=repo,
            repo_files=codebase,
            command_list=init_commands,
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
                if last_command.status == CommandStatus.SUCCESS:
                    max_len = 500
                    if len(output_str) > max_len:
                        output_str = f"Output too long: ... {output_str[-max_len:]}"
                    conversation.add_tool_response(
                        tool_id=ai_action.id,
                        message=output_str,
                    )
                else:
                    conversation.add_tool_response(
                        tool_id=ai_action.id,
                        message=f"{output_str}\n\nERROR: Command timed out...\n",
                    )
                    conversation.add_user(
                        "Verify if the command executed successfully."
                    )
        state.persist()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("ticket", type=str)
    parser.add_argument("repo", type=str)
    parser.add_argument("context", type=str)
    parser.add_argument("--name", type=str, default=None)
    args = parser.parse_args()

    states_dir = f"db/{AGENT}/"
    if args.name:
        state = State.load(args.name, AGENT)
    else:
        state = State(
            name=str(time.time()), agent=AGENT, conversation=Conversation(), pr=None
        )
    context_state = State.load(args.context, PM_AGENT)

    run(context_state, state, repo=args.repo, ticket_key=args.ticket)
