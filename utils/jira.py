import os
import requests
from requests.auth import HTTPBasicAuth
import json
from typing import Any, Dict, Literal, Optional

URL = os.environ["JIRA_URL"]
AUTH = HTTPBasicAuth(os.environ["JIRA_EMAIL"], os.environ["JIRA_API_KEY"])


def create_issue(
    issue_type: Literal["Epic", "Story", "Task", "Subtask"],
    summary: str,
    description: str,
    parent_key: Optional[str] = None,
) -> Dict[str, Any]:
    issue_data = {
        "fields": {
            "project": {"key": "SBX"},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"text": description, "type": "text"}],
                    }
                ],
            },
            "issuetype": {"name": issue_type},
        }
    }
    if parent_key:
        issue_data["fields"]["parent"] = {"key": parent_key}

    response = requests.post(
        URL,
        data=json.dumps(issue_data),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        auth=AUTH,
    )
    return response.json()
