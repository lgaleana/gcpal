import argparse
import time
import traceback

from dotenv import load_dotenv

load_dotenv()

from ai_tools import sumamrize_test_failure
from agents import contributor
from workflows.write_pr import AGENT as CODER_AGENT, TOOL_FAIL_MSG
from tools import github
from tools.docker.commands import DockerRunner
from utils.io import user_input, print_system
from utils.state import Conversation, State
from workflows.actions.coder_actions import TestsError
from workflows.actions.contributor_actions import edit_pr, rollback


AGENT = "contributor"


def run(context_state: State, state: State) -> None:
    assert context_state.pr
    pr = context_state.pr

    docker = DockerRunner(
        startup_commands=[
            "cd /home/app",
            "pwd",
            "source venv/bin/activate",
            "git checkout main",
            "git pull origin main --rebase",
        ]
    )

    conversation = state.conversation
    acted_comments = state.acted_comments

    comments = github.get_comments(
        pr.number, username="lgaleana-llm", skip_ids=acted_comments
    )
    if not comments:
        print_system("No new comments.")
        return
    comment = comments[0]

    conversation.add_user("You have a new comment in the PR:")
    print_system(comment)
    conversation.add_system(str(comment))

    ai_action = contributor.next_action(
        context_state.conversation, conversation, pr.number
    )
    if isinstance(ai_action, str):
        conversation.add_assistant(ai_action)
        user_message = user_input()
        if user_message == "y":
            github.reply_to_comment(pr.number, comment.id, reply=ai_action)
            print_system("Comment saved ::")
            conversation.add_system("Comment saved. Next comment...")
        else:
            print_system("Comment not saved.")
        return

    while True:
        tool = contributor.AmendPRParams(original=pr, **ai_action.arguments)
        print_system(tool)
        conversation.add_tool(tool=ai_action)

        user_message = user_input()
        if user_message != "y":
            print_system("PR not amended.")
            return

        try:
            state.pr = edit_pr(tool, state.name, docker)
            conversation.add_tool_response(
                tool_id=ai_action.id,
                message=(f"PR amended successfully :: {state.pr}"),
            )
            print_system(state.pr)
            break
        except Exception as e:
            print_system()
            print_system(f"!!!!! ERROR\n: {e}")
            traceback.print_tb(e.__traceback__)
            print_system()

            rollback(pr, docker)
            conversation.remove_last_failed_tool(TOOL_FAIL_MSG)

            if isinstance(e, TestsError):
                conversation.add_tool_response(
                    tool_id=ai_action.id,
                    message=sumamrize_test_failure(pr=tool, failure_msg=str(e)),
                )
                conversation.add_user(TOOL_FAIL_MSG)
            else:
                conversation.add_tool_response(
                    tool_id=ai_action.id,
                    message=str(e),
                )

            ai_action = contributor.next_action(
                context_state.conversation, conversation, pr.number
            )
            assert not isinstance(ai_action, str)

    acted_comments.append(comment.id)
    state.persist()
    print_system(state.name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
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
    context_state = State.load(args.context, CODER_AGENT)

    run(context_state, state)
