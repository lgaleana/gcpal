import argparse

from dotenv import load_dotenv

load_dotenv()

from ai_tools import summarize_architecture
from utils.io import print_assistant
from utils.state import State
from workflows.plan_project import AGENT as PM_AGENT


def run(state: State):
    conversation = state.conversation
    summary = summarize_architecture(conversation)
    state.project_description = summary.project_description
    state.project_architecture = summary.architecture_overview
    print_assistant(summary.project_description)
    print_assistant(summary.architecture_overview)
    breakpoint()

    state.persist()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("context", type=str)
    args = parser.parse_args()
    context_state = State.load(args.context, PM_AGENT)

    run(context_state)
