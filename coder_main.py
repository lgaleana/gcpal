import json

from dotenv import load_dotenv

load_dotenv()

from ai_tasks import coder
from utils import github
from utils import jira
from utils.io import user_input, print_system
from utils.state import Conversation


def run() -> None:
    conversation = Conversation()
    tickets = jira.get_grouped_issues()
    codebase = github.get_repo_files()
    git_history = github.get_last_commits(n=10)
    active_ticket = jira.find_issue(tickets, "SBX-50")
    assert active_ticket

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
            print_system(tool.title)
            print_system(tool.description)
            print_system(tool.test_plan)
            print_system(tool.diff_file)
            conversation.add_tool(
                tool_id=ai_action.id, arguments=json.dumps(ai_action.arguments)
            )
            user_message = user_input()
            conversation.add_tool_response(
                tool_id=ai_action.id, message=f"Response: {user_message}"
            )


if __name__ == "__main__":
    run()
