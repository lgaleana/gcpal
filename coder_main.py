import json

from dotenv import load_dotenv

load_dotenv()

from ai_tasks import coder
from utils import docker
from utils.io import user_input, print_system
from utils.state import Conversation


def run(feature: str) -> None:
    conversation = Conversation()
    initial_commands = docker.coder()
    while True:
        ai_action = coder.next_action(feature, initial_commands, conversation)
        if isinstance(ai_action, str):
            conversation.add_assistant(ai_action)
            user_message = user_input()
            conversation.add_user(user_message)
        else:
            print_system(ai_action.arguments)
            conversation.add_tool(
                tool_id=ai_action.id, arguments=json.dumps(ai_action.arguments)
            )
            user_message = user_input()
            conversation.add_tool_response(
                tool_id=ai_action.id, message=f"Response: {user_message}"
            )
