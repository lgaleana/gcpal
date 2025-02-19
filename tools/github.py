import base64
import os
import requests
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional, Union

from utils.io import print_system


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


class PullRequest(BaseModel):
    number: int
    title: str
    description: str
    test_plan: str
    head: str
    base: str
    html_url: str
    commits: List[str] = []


class GithubComment(BaseModel):
    id: int
    author: str
    body: str
    created_at: datetime
    html_url: str
    node_id: str

    def __str__(self) -> str:
        return f"@{self.author}:\n  {self.body}"


class PRCreationError(Exception):
    pass


class ReviewComment(GithubComment):
    line: int
    diff_hunk: str

    def __str__(self) -> str:
        return (
            f"@{self.author}:\n"
            f"```\n{self.diff_hunk}\n```\n\n"
            f"line {self.line}: {self.body}"
        )


def get_repo_files(repo: str, branch: str = "main") -> List[Optional[GithubFile]]:
    response = requests.get(
        f"https://api.github.com/repos/lgaleana/{repo}/git/trees/{branch}?recursive=1",
        headers=HEADERS,
    )
    response.raise_for_status()

    file_contents = []
    repo_data = response.json()
    for file in repo_data["tree"]:
        if file["type"] == "blob":  # Make sure it's a file
            file_contents.append(get_file_contents(file["path"], repo=repo))
    return file_contents


def get_file_contents(file_path: str, repo: str) -> Optional[GithubFile]:
    response = requests.get(
        f"https://api.github.com/repos/lgaleana/{repo}/contents/{file_path}",
        headers=HEADERS,
    )
    response.raise_for_status()

    file_data = response.json()
    # TODO: Make this more generic
    if file_path.endswith("package-lock.json") or file_path.endswith("package.json"):
        content = "..."
    else:
        # Decode the base64 content
        try:
            content = base64.b64decode(file_data["content"]).decode("utf-8")
        except:
            content = "..."
    return GithubFile(path=file_path, content=content)


def get_last_commits(n: int, repo: str):
    response = requests.get(f"https://api.github.com/repos/lgaleana/{repo}/commits")
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
    head: str, base: str, title: str, description: str, test_plan: str, repo: str
) -> PullRequest:
    body = f"{description}\n\n### Test Plan\n\n{test_plan}"
    response = requests.post(
        f"https://api.github.com/repos/lgaleana/{repo}/pulls",
        headers=HEADERS,
        json={"title": title, "body": body, "head": head, "base": base},
    )
    if response.status_code < 200 or response.status_code >= 300:
        raise PRCreationError(response.text)

    response = response.json()
    return PullRequest(
        number=response["number"],
        title=title,
        description=description,
        test_plan=test_plan,
        head=head,
        base=base,
        html_url=response["html_url"],
        commits=[response["head"]["sha"]],
    )


def get_review_comments(pr_number: int, repo: str) -> List[GithubComment]:
    response = requests.get(
        f"https://api.github.com/repos/lgaleana/{repo}/pulls/{pr_number}/comments",
        headers=HEADERS,
    )
    response.raise_for_status()
    response = response.json()
    return [
        ReviewComment(
            id=c["id"],
            author=c["user"]["login"],
            body=c["body"],
            created_at=datetime.strptime(c["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
            html_url=c["html_url"],
            line=c["line"] or c["original_line"],
            diff_hunk=c["diff_hunk"],
            node_id=c["node_id"],
        )
        for c in response
    ]


def get_issue_comments(pr_number: int, repo: str) -> List[GithubComment]:
    response = requests.get(
        f"https://api.github.com/repos/lgaleana/{repo}/issues/{pr_number}/comments",
        headers=HEADERS,
    )
    response.raise_for_status()
    response = response.json()
    return [
        GithubComment(
            id=c["id"],
            author=c["user"]["login"],
            body=c["body"],
            created_at=datetime.strptime(c["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
            html_url=c["html_url"],
            node_id=c["node_id"],
        )
        for c in response
    ]


def get_comments(
    pr_number: int, username: str, skip_ids: List[int], repo: str
) -> List[Union[ReviewComment, GithubComment]]:
    review_comments = get_review_comments(pr_number, repo)
    issue_comments = get_issue_comments(pr_number, repo)

    all_comments = []
    for comment in sorted(review_comments + issue_comments, key=lambda c: c.created_at):
        if comment.author != username and comment.id not in skip_ids:
            all_comments.append(comment)
    return all_comments


def reply_to_comment(
    pr_number: int, comment_id: int, reply: str, repo: str
) -> ReviewComment:
    response = requests.post(
        f"https://api.github.com/repos/lgaleana/{repo}/pulls/{pr_number}/comments/{comment_id}/replies",
        json={"body": reply},
        headers=HEADERS,
    )
    response.raise_for_status()
    c = response.json()
    return ReviewComment(
        id=c["id"],
        author=c["user"]["login"],
        body=c["body"],
        created_at=datetime.strptime(c["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
        html_url=c["html_url"],
        line=c["line"],
        diff_hunk=c["diff_hunk"],
        node_id=c["node_id"],
    )
