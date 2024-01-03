from typing import Literal, Optional, Union

from pydantic import BaseModel, Field

from ai import llm
from utils.jira import IssueType
from utils.state import Conversation


class Action:
    CHAT = "chat"
    FILE_ISSUE = "file_issue"


class FileIssueParams(BaseModel):
    type_: IssueType = Field(description="Type of the issue")
    title: str = Field(description="Title of the issue")
    description: str = Field(description="Description of the issue")
    parent_key: Optional[str] = Field(None, description="Parent of the issue")


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": Action.FILE_ISSUE,
            "description": "Executes shell commands in Ubuntu",
            "parameters": FileIssueParams.schema(),
        },
    },
]


class Tool(llm.RawTool):
    arguments: FileIssueParams


class NextAction(BaseModel):
    name: str
    payload: Union[str, Tool]


PROMPT = """You are a helpful AI assistant that helps software engineers plan and design their software projects.

A software project is structured in the following way:
- Epic: A big user story that needs to be broken down. In agile development, epics usually represent a significant deliverable, such as a new feature or experience.
- Story: A high-level goal in the eyes of the user. They should be written from the users' point of view.
- Subtask: The most atomic piece of work that is required to complete a task. Subtasks cannot be subdivided.

Your goal is to work with the user and provide suggestions until they are satisfied with the breakdown of their project.
As you work with the user, you can do it in a top-down fashion. That is:
1. Brief description of the epics. Agree on the epics.
2. For each epic,
    - Brief description of the stories.
    - Agree on the stories.
3. For each story,
    - Brief description of the subtasks.
    - Agree on the subtasks.

Say hi."""


def next_action(conversation: Conversation) -> Union[str, Tool]:
    next = llm.stream_next(
        [{"role": "system", "content": PROMPT}] + conversation,
        tools=TOOLS,
    )

    if isinstance(next, str):
        return next
    return Tool(
        id=next.id,
        name=next.name,
        arguments=FileIssueParams.parse_obj(next.arguments),
    )
