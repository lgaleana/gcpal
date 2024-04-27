import argparse
import time
import traceback

from dotenv import load_dotenv

load_dotenv()

from ai_tools import sumamrize_test_failure, there_is_followup
from agents import contributor
from workflows.write_pr import AGENT as CODER_AGENT, TOOL_FAIL_MSG
from tools import github
from tools.docker.commands import DockerRunner
from utils.io import print_system
from utils.state import Conversation, State
from workflows.actions.coder_actions import TestsError
from workflows.actions.contributor_actions import edit_pr, rollback


AGENT = "contributor"


def run(context_state: State, repo: str, state: State) -> None:
    assert state.pr

    pr = state.pr
    state.pr = pr
    acted_comments = state.acted_comments
    context_state.conversation.add_system(f"Pull Request created successfully:\n{pr}")

    comments = github.get_comments(
        pr.number,
        username="lgaleana-llm",
        skip_ids=acted_comments,
        repo=repo,
    )
    if not comments:
        print_system("No new comments.")
        return
    comment = comments[0]

    codebase = github.get_repo_files(repo=repo)

    docker = DockerRunner(
        startup_commands=[
            f"cd /home/{repo}",
            "pwd",
            "source venv/bin/activate",
            "git checkout main",
            "git pull origin main --rebase",
        ]
    )

    conversation = state.conversation
    conversation.add_user(f"You have a new comment in the PR:\n{comment}")
    print_system(comment)

    while True:
        ai_action = contributor.next_action(
            conversation_context=context_state.conversation,
            conversation=conversation,
            repo_files=codebase,
        )
        if isinstance(ai_action, str):
            conversation.add_assistant(ai_action)
            # user_message = user_input()
            # if user_message == "y":
            assistant_comment = github.reply_to_comment(
                pr.number,
                comment.id,
                reply=ai_action,
                repo=repo,
            )
            print_system(f"Comment saved :: {assistant_comment}")
            conversation.add_system("Comment saved.")

            if not there_is_followup(assistant_comment.body):
                # There are cases where the agent replies, but
                # the next action should immediately be to amend the PR
                break
            # else:
            #     print_system("Comment not saved.")
            #     break
        else:
            tool = contributor.AmendPRParams(original=pr, **ai_action.arguments)
            print_system(tool)
            conversation.add_tool(tool=ai_action)

            try:
                state.pr = edit_pr(tool, state.name, docker, repo=repo)
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

                if isinstance(e, TestsError):
                    conversation.remove_last_failed_tool(TOOL_FAIL_MSG)
                    conversation.add_tool_response(
                        tool_id=ai_action.id,
                        message=sumamrize_test_failure(
                            pr=tool, failure_msg=str(e), repo_files=codebase
                        ),
                    )
                    conversation.add_user(TOOL_FAIL_MSG)
                else:
                    conversation.add_tool_response(
                        tool_id=ai_action.id,
                        message=str(e),
                    )
        state.persist()

    conversation.remove_last_failed_tool(TOOL_FAIL_MSG)
    acted_comments.append(comment.id)
    state.final_persist(f"{context_state.name.split('-')[0]}_{pr.number}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("context", type=str)
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
    context_state = State.load(args.context, CODER_AGENT)
    state.pr = context_state.pr

    run(context_state, args.repo, state)
