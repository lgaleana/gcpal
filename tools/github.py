import base64
import os
import requests
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional


GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}


class GithubFile(BaseModel):
    path: str
    content: str

    def __str__(self) -> str:
        return f"{self.path}\n" "```\n" f"{self.content}\n" "```"


class Commit(BaseModel):
    sha: str
    author: str
    date: datetime
    message: str

    def __str__(self) -> str:
        date = self.date.strftime("%a %b %d %H:%M:%S %Y")
        return (
            "commit {self.sha}\n"
            f"Author: {self.author}\n"
            f"Date:   {date}\n\n"
            f"    {self.message}"
        )


class GithubComment(BaseModel):
    id: int
    author: str
    body: str
    created_at: datetime
    diff_hunk: Optional[str] = None


def get_repo_files() -> List[Optional[GithubFile]]:
    response = requests.get(
        "https://api.github.com/repos/lgaleana/email-sequences/git/trees/main?recursive=1",
        headers=HEADERS,
    )
    response.raise_for_status()

    file_contents = []
    repo_data = response.json()
    for file in repo_data["tree"]:
        if file["type"] == "blob":  # Make sure it's a file
            file_contents.append(get_file_contents(file["path"]))
    return file_contents


def get_file_contents(file_path: str) -> Optional[GithubFile]:
    response = requests.get(
        f"https://api.github.com/repos/lgaleana/email-sequences/contents/{file_path}",
        headers=HEADERS,
    )
    if response.status_code == 200:
        file_data = response.json()
        # Decode the base64 content
        content = base64.b64decode(file_data["content"]).decode("utf-8")
        return GithubFile(path=file_path, content=content)

    return None


def get_last_commits(n: int):
    response = requests.get(
        "https://api.github.com/repos/lgaleana/email-sequences/commits"
    )
    response.raise_for_status()
    commits = response.json()
    return [
        Commit(
            sha=c["sha"],
            author=c["commit"]["author"]["name"],
            date=datetime.fromisoformat(c["commit"]["author"]["date"]),
            message=c["commit"]["message"],
        )
        for c in commits[:n]
    ]


def create_pr(
    head: str, base: str, title: str, description: str, test_plan: str
) -> str:
    body = f"{description}\n\n### Test Plan\n\n{test_plan}"
    response = requests.post(
        "https://api.github.com/repos/lgaleana/email-sequences/pulls",
        headers=HEADERS,
        json={"title": title, "body": body, "head": head, "base": base},
    )
    response.raise_for_status()
    return response.json()["html_url"]


def get_review_comments(pr_number: int) -> List[GithubComment]:
    response = requests.get(
        f"https://api.github.com/repos/lgaleana/email-sequences/pulls/{pr_number}/comments",
        headers=HEADERS,
    )
    response.raise_for_status()
    return [
        GithubComment(
            id=c["id"],
            author=c["user"]["login"],
            body=c["body"],
            created_at=datetime.strptime(c["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
            diff_hunk=c["diff_hunk"],
        )
        for c in response.json()
    ]


def get_issue_comments(pr_number: int) -> List[GithubComment]:
    response = requests.get(
        f"https://api.github.com/repos/lgaleana/email-sequences/issues/{pr_number}/comments",
        headers=HEADERS,
    )
    response.raise_for_status()
    return [
        GithubComment(
            id=c["id"],
            author=c["user"]["login"],
            body=c["body"],
            created_at=datetime.strptime(c["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
        )
        for c in response.json()
    ]


def get_comments_since(pr_number: int, username: str) -> List[GithubComment]:
    review_comments = get_review_comments(pr_number)
    issue_comments = get_issue_comments(pr_number)
    all_comments = sorted(review_comments + issue_comments, key=lambda c: c.created_at)

    # Find the last comment by the user
    last_user_comment_index = -1
    for i, comment in enumerate(all_comments):
        if comment.author == username:
            last_user_comment_index = i

    # All comments after the user's last comment
    return all_comments[last_user_comment_index + 1 :]


def reply_to_comment(pr_number: int, comment_id: int, reply: str) -> None:
    response = requests.post(
        f"https://api.github.com/repos/lgaleana/email-sequences/issues/{pr_number}/comments",
        json={"body": reply, "in_reply_to": comment_id},
        headers=HEADERS,
    )
    response.raise_for_status()
    print(response.json())


def reply_to_comment_gql(node_id: str, reply: str) -> None:
    query = """
    mutation {
      addPullRequestReviewComment(input: {
        pullRequestReviewId: "%s",
        body: "%s"
      }) {
        comment {
          body
        }
      }
    }
    """ % (
        node_id,
        reply,
    )

    response = requests.post(
        "https://api.github.com/graphql", json={"query": query}, headers=HEADERS
    )
    response.raise_for_status()
    print(response.text)
