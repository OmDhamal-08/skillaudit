"""Load a skill straight from GitHub using the contents API.

Files are downloaded as text and never executed. We use the API instead of
`git clone` so there is no git dependency, we can fetch just one sub-folder of a
big repo, and size limits are checked (from the listing) before anything is downloaded.
"""

import os
import re

import httpx

from ..config import MAX_FILE_BYTES, MAX_FILES
from ..models import SkillBundle, SkillFile
from .common import LoaderError, build_bundle, make_file

API = "https://api.github.com"

# https://github.com/<owner>/<repo>[/tree|blob/<ref>[/<path>]]
URL_PATTERN = re.compile(
    r"^https://github\.com/([\w.-]+)/([\w.-]+?)(?:\.git)?"
    r"(?:/(tree|blob)/([^/]+)(?:/(.*?))?)?/?$"
)


def parse_github_url(url: str) -> tuple[str, str, str | None, str]:
    """Return (owner, repo, ref, path). ref is None when the URL has no branch."""
    match = URL_PATTERN.match(url.strip())
    if not match:
        raise LoaderError(f"Not a GitHub repo/tree/blob URL: {url}")
    owner, repo, _kind, ref, path = match.groups()
    return owner, repo, ref, (path or "")


def _client() -> httpx.Client:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "skillaudit"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return httpx.Client(headers=headers, timeout=20, follow_redirects=True)


def load_github(url: str, client: httpx.Client | None = None,
                max_files: int = MAX_FILES, max_bytes: int = MAX_FILE_BYTES) -> SkillBundle:
    owner, repo, ref, root = parse_github_url(url)
    client = client or _client()
    files: list[SkillFile] = []
    notes: list[str] = []
    truncated = False

    # Breadth-first walk over folders. A plain list as a queue is enough here.
    pending = [root]
    single_file = False
    while pending and not truncated:
        listing = _get_contents(client, owner, repo, pending.pop(0), ref)
        if isinstance(listing, dict):        # the URL pointed at one file, not a folder
            listing = [listing]
            single_file = True

        for item in listing:
            if item["type"] == "dir":
                pending.append(item["path"])
                continue
            if len(files) >= max_files:
                truncated = True
                break

            rel = _relative(item["path"], root) or item["name"]
            if item["type"] != "file":       # symlink or submodule: never follow
                files.append(SkillFile(path=rel, skip_reason="symlink"))
            elif item["size"] > max_bytes:
                files.append(SkillFile(path=rel, skip_reason="too_large"))
            else:
                files.append(make_file(rel, _download(client, item["download_url"]), max_bytes))

    if truncated:
        notes.append(f"Stopped after {max_files} files; the rest of the repo was not scanned.")
    if single_file:
        notes.append("URL points at a single file; the rest of the skill was not scanned.")
    if not files:
        raise LoaderError(f"No files found at {url}")
    return build_bundle(f"github:{url}", files, partial=truncated or single_file, notes=notes)


def _get_contents(client: httpx.Client, owner: str, repo: str, path: str, ref: str | None):
    params = {"ref": ref} if ref else None
    try:
        response = client.get(f"{API}/repos/{owner}/{repo}/contents/{path}", params=params)
    except httpx.HTTPError as exc:
        raise LoaderError(f"Could not reach GitHub: {exc}") from exc
    if response.status_code == 404:
        raise LoaderError(f"Not found: {owner}/{repo}/{path} (private repo? set GITHUB_TOKEN)")
    if response.status_code == 403 and response.headers.get("x-ratelimit-remaining") == "0":
        raise LoaderError("GitHub API rate limit reached. Set GITHUB_TOKEN to get a higher limit.")
    if response.status_code != 200:
        raise LoaderError(f"GitHub API error {response.status_code} for {path or '/'}")
    return response.json()


def _download(client: httpx.Client, download_url: str) -> bytes:
    try:
        response = client.get(download_url)
    except httpx.HTTPError as exc:
        raise LoaderError(f"Could not download {download_url}: {exc}") from exc
    if response.status_code != 200:
        raise LoaderError(f"Could not download {download_url} ({response.status_code})")
    return response.content


def _relative(path: str, root: str) -> str:
    if root and path.startswith(root):
        return path[len(root):].lstrip("/")
    return path
