from typing import List, Optional

from pydantic import BaseModel, Field

from ai import llm
from ai_tasks.chat import Tool
from utils.github import GithubFile, Commit
from utils.jira import Issue
from utils.state import Conversation


class Action:
    WRITE_PR = "write_pr"


class WritePRParams(BaseModel):
    title: str = Field(description="Title of the PR")
    description: str = Field(description="Description of the PR")
    test_plan: str = Field(description="How did you test this PR?")
    diff_file: str = Field(
        description="The actual content of the PR, in the format of a diff file"
    )


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": Action.WRITE_PR,
            "description": "Writes a Pull Request",
            "parameters": WritePRParams.schema(),
        },
    },
]


PROMPT = """You are a helpful AI assistant that writes code and creates Pull Requests.

You are working in the following project

### Project description

FastAPI application that lets users schedule email sequences to be delivered in the future.

### Architecture overview

1. **Frontend (User Interface)**: This will be a single page application where users can create, view, edit, and delete email schedules and sequences. It will also display the status of scheduled emails and sequences. The frontend will communicate with the backend via API calls.
2. **Backend (FastAPI)**: This will handle all the server-side logic of your application. It will have various API endpoints for handling requests related to email schedules and sequences. The backend will be responsible for validating requests, interacting with the database, and returning responses.
3. **Database**: This will store all the data related to email schedules and sequences, as well as the status of each scheduled email and sequence. The database schema will be designed to efficiently store and retrieve this data.
4. **Job Scheduler**: This will be a separate process that runs at regular intervals. It will fetch scheduled emails and sequences from the database and send them out in the correct order. It will also update the status of each email and sequence in the database.
5. **Email Service**: This will be responsible for the actual sending of emails. The job scheduler will interact with this service to send out the emails.
This architecture separates concerns into distinct components, each responsible for a specific part of the application. This makes the application easier to develop, test, and maintain. It also allows for scalability, as each component can be scaled independently based on its specific load and performance requirements.

### Project tickets

{jira}

### Codebase

```
{codebase}
```

### Last 10 commits

```
{git}
```

### Requirements

1. Follow the best software engineering practices.
2. Consider the existing code and the current file structure.
3. The PR content must be in the format of a diff file.
4. Include unit tests in the PR. Use mocked data.

### The ticket assigned to you

{ticket}"""


def next_action(
    ticket: Issue,
    conversation: Conversation,
    all_tickets: List[Issue],
    repo_files: List[Optional[GithubFile]],
    commits: List[Commit],
):
    next = llm.stream_next(
        [
            {
                "role": "user",
                "content": PROMPT.format(
                    ticket=ticket,
                    jira="\n".join(str(t) for t in all_tickets),
                    codebase="\n".join(str(f) for f in repo_files),
                    git="\n".join(str(c) for c in commits),
                ),
            }
        ]
        + conversation,
        tools=TOOLS,
    )
    return next
