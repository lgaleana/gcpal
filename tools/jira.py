import os
import requests
from requests.auth import HTTPBasicAuth
import json
from pydantic import BaseModel
from typing import Any, Dict, List, Literal, Optional

DOMAIN = "https://lsgaleana.atlassian.net/rest/api/3"
AUTH = HTTPBasicAuth(os.environ["JIRA_EMAIL"], os.environ["JIRA_API_KEY"])
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}


IssueType = Literal["Epic", "Story", "Subtask"]


class Issue(BaseModel):
    type_: IssueType
    key: str
    title: str
    description: str
    status: str
    children: List["Issue"]
    parent_key: Optional[str] = None

    def __str__(self) -> str:
        return (
            f"{self.key}: {self.type_} - {self.title}\n"
            f"{self.description}\n"
            f"Status: {self.status}"
        )


def create_issue(
    issue_type: IssueType,
    project_key: str,
    summary: str,
    description: str,
    parent_key: Optional[str] = None,
) -> Dict[str, Any]:
    issue_data = {
        "fields": {
            "project": {"key": project_key},
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
        f"{DOMAIN}/issue",
        data=json.dumps(issue_data),
        headers=HEADERS,
        auth=AUTH,
    )
    return response.json()


def get_all_issues() -> List[Dict[str, Any]]:
    jql_query = "project=SBX AND issuetype in ('Epic', 'Story', 'Subtask')"
    response = requests.get(
        f"{DOMAIN}/search?jql={jql_query}", headers=HEADERS, auth=AUTH
    )
    return response.json().get("issues", [])


def get_grouped_issues() -> List[Issue]:
    all_issues = get_all_issues()

    epics = {}
    stories = {}
    subtasks = []
    for raw_issue in all_issues:
        issue = Issue(
            type_=raw_issue["fields"]["issuetype"]["name"],
            key=raw_issue["key"],
            title=raw_issue["fields"]["summary"],
            description=raw_issue["fields"]["description"]["content"][0]["content"][0][
                "text"
            ],
            status=raw_issue["fields"]["status"]["name"],
            children=[],
            parent_key=raw_issue["fields"].get("parent", {}).get("key"),
        )
        if issue.type_ == "Epic":
            epics[issue.key] = issue
        elif issue.type_ == "Story":
            stories[issue.key] = issue
        elif issue.type_ == "Subtask":
            subtasks.append(issue)

    for story in stories.values():
        epics[story.parent_key].children.append(story)
    for subtask in subtasks:
        stories[subtask.parent_key].children.append(subtask)

    return list(epics.values())


def find_issue(issues: List[Issue], key: str) -> Optional[Issue]:
    for issue in issues:
        if issue.key.lower() == key.lower():
            return issue

        found_issue = find_issue(issue.children, key)
        if found_issue:
            return found_issue

    return None
