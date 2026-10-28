"""Draft pull requests on GitHub, opened by plain code after the boss approves a data-update proposal.

Nothing here decides what goes into a pull request: the office hands over one finished proposal file, and this client
refuses anything else. The limits are enforced in code, whatever any AI wrote:

- the only file it can add sits under sources/audit/proposals/ and is a small JSON object;
- the branch is always office/…, created from the tip of the base branch, never the base branch itself;
- the pull request is always a draft;
- there is no call that merges, closes, deletes or force-pushes, so the merge button stays yours.

The token comes from `office auth github` or OFFICE_GITHUB_TOKEN. Give it a fine-grained token for this one
repository (Contents and Pull requests: read and write); see README.
"""

from __future__ import annotations

import base64
import json
import re
from typing import Any
from urllib.parse import quote

from .base import Client, PlatformError

API = "https://api.github.com"
REPO = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9._-]{1,100}")
BASE_BRANCH = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,100}")
BRANCH = re.compile(r"office/[A-Za-z0-9._-]{1,80}")
PROPOSAL_DIR = "sources/audit/proposals"
PROPOSAL_FILE = re.compile(r"sources/audit/proposals/\d{4}-\d{2}-\d{2}-[a-z0-9_]{1,40}-[0-9a-f]{8}\.json")
MAX_FILE_BYTES = 40_000
MAX_TITLE, MAX_BODY = 200, 20_000
# Classic tokens (ghp_…) reach every repository of the account; fine-grained ones (github_pat_…) only the chosen one.
CLASSIC_PREFIXES = ("ghp_", "gho_", "ghu_", "ghs_")


def is_classic_token(token: str) -> bool:
    return token.startswith(CLASSIC_PREFIXES)


class GitHubClient(Client):
    name = "GitHub"

    def __init__(self, repo: str, token: str, *, base: str = "main", api: str = API, **kwargs):
        super().__init__(**kwargs)
        self.repo, self.token, self.base, self.api = repo, token, base, api.rstrip("/")

    # ---- plumbing ----
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "uniway-marketing-office",
        }

    def _call(self, method: str, path: str, *, json: Any = None, params: dict | None = None, fake: Any = None) -> Any:
        response = self.request(method, f"{self.api}{path}", params=params, json=json, headers=self._headers(), fake=fake)
        if self.dry_run:
            return fake
        return response.json() if response.content else {}

    def _ready(self) -> None:
        """Checked when a call is made, not when the client is built, so a typo here cannot stop the other platforms."""
        if not REPO.fullmatch(self.repo):
            raise PlatformError(f"GitHub repo「{self.repo}」要寫成 擁有者/名稱（OFFICE_GITHUB_REPO）")
        if not BASE_BRANCH.fullmatch(self.base) or ".." in self.base:
            raise PlatformError(f"GitHub 基底分支「{self.base}」看起來不對（OFFICE_GITHUB_BASE）")
        if not self.token and not self.dry_run:
            raise PlatformError("還沒有 GitHub 權杖：uv run office auth github")

    # ---- reading (used by `office auth github` and `office check`) ----
    def check(self) -> dict:
        """Who the token is and whether it can push to the repository. Reads only; nothing is created."""
        self._ready()
        try:
            login = (self._call("GET", "/user", fake={"login": ""}) or {}).get("login", "")
        except PlatformError:  # some fine-grained tokens cannot read the user; the repository is what matters
            login = ""
        repo = self._call("GET", f"/repos/{self.repo}", fake={"full_name": self.repo, "private": False, "permissions": {"push": True}})
        self._call("GET", f"/repos/{self.repo}/branches/{quote(self.base, safe='/')}", fake={})
        return {
            "login": login,
            "repo": repo.get("full_name", self.repo),
            "private": bool(repo.get("private")),
            "can_push": bool((repo.get("permissions") or {}).get("push")),
        }

    # ---- the one thing this client writes ----
    def open_draft_pr(self, *, branch: str, path: str, content: str, commit_message: str, title: str, body: str) -> dict:
        """Branch off the base branch, add the proposal file, open a draft pull request: {"id", "url"}.

        Every step tolerates an earlier attempt that stopped half way (the branch, the file or the pull request is
        already there), so approving a failed proposal again finishes the job instead of failing on step two."""
        self._ready()
        self._check_request(branch, path, content, title, body)
        repo, base = f"/repos/{self.repo}", quote(self.base, safe="/")
        tip = self._call("GET", f"{repo}/git/ref/heads/{base}", fake={"object": {"sha": "0" * 40}})["object"]["sha"]
        try:
            self._call("POST", f"{repo}/git/refs", json={"ref": f"refs/heads/{branch}", "sha": tip}, fake={})
        except PlatformError as error:
            if error.status != 422:  # 422: the branch exists from an earlier attempt
                raise
        encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
        try:
            self._call("PUT", f"{repo}/contents/{quote(path)}", fake={},
                       json={"message": commit_message.splitlines()[0][:200] if commit_message.strip() else "office proposal",
                             "content": encoded, "branch": branch})
        except PlatformError as error:
            if error.status != 422 or not self._same_file_on(branch, path, content):
                raise
        try:
            pr = self._call("POST", f"{repo}/pulls", fake={"number": self.fake_id("pr"), "html_url": ""},
                            json={"title": title[:MAX_TITLE], "head": branch, "base": self.base, "body": body, "draft": True,
                                  "maintainer_can_modify": False})
        except PlatformError as error:
            pr = self._open_pr_from(branch) if error.status == 422 else None
            if not pr:
                raise
        return {"id": str(pr.get("number", "")), "url": pr.get("html_url", "")}

    # ---- the limits ----
    def _check_request(self, branch: str, path: str, content: str, title: str, body: str) -> None:
        if not BRANCH.fullmatch(branch) or ".." in branch or branch.endswith((".", ".lock")) or branch == self.base:
            raise PlatformError(f"分支名稱「{branch}」不合規則：只能是 office/ 開頭的新分支")
        if not PROPOSAL_FILE.fullmatch(path):
            raise PlatformError(f"只能新增 {PROPOSAL_DIR}/ 底下的提案檔，不能動「{path[:80]}」")
        if len(content.encode("utf-8")) > MAX_FILE_BYTES:
            raise PlatformError(f"提案檔太大（上限 {MAX_FILE_BYTES // 1000} KB）")
        try:
            valid = isinstance(json.loads(content), dict)
        except ValueError:
            valid = False
        if not valid:
            raise PlatformError("提案檔必須是一個 JSON 物件")
        if not title.strip() or len(body) > MAX_BODY:
            raise PlatformError(f"PR 標題不能空白，說明不能超過 {MAX_BODY} 字")

    def _same_file_on(self, branch: str, path: str, content: str) -> bool:
        """After "already exists": is the file on the branch exactly what we meant to add?"""
        try:
            found = self._call("GET", f"/repos/{self.repo}/contents/{quote(path)}", params={"ref": branch}, fake={}) or {}
            return base64.b64decode(found.get("content", "")).decode("utf-8") == content
        except (PlatformError, ValueError):
            return False

    def _open_pr_from(self, branch: str) -> dict | None:
        owner = self.repo.split("/")[0]
        found = self._call("GET", f"/repos/{self.repo}/pulls", params={"head": f"{owner}:{branch}", "state": "open"}, fake=[])
        return found[0] if isinstance(found, list) and found else None
