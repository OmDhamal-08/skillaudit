import httpx
import pytest

from skillaudit.loaders import LoaderError
from skillaudit.loaders.github import load_github, parse_github_url


@pytest.mark.parametrize("url, expected", [
    ("https://github.com/acme/skills", ("acme", "skills", None, "")),
    ("https://github.com/acme/skills.git", ("acme", "skills", None, "")),
    ("https://github.com/acme/skills/tree/main/pdf-helper/", ("acme", "skills", "main", "pdf-helper")),
    ("https://github.com/acme/skills/tree/v1.2/skills/pdf", ("acme", "skills", "v1.2", "skills/pdf")),
    ("https://github.com/acme/skills/blob/main/pdf/SKILL.md", ("acme", "skills", "main", "pdf/SKILL.md")),
])
def test_parse_github_url(url, expected):
    assert parse_github_url(url) == expected


@pytest.mark.parametrize("url", ["https://gitlab.com/a/b", "https://github.com/onlyowner", "not a url"])
def test_parse_github_url_rejects_other_urls(url):
    with pytest.raises(LoaderError):
        parse_github_url(url)


def fake_github(routes: dict, status: dict | None = None, headers: dict | None = None) -> httpx.Client:
    """An httpx client that answers from a dict instead of the network."""
    def handler(request: httpx.Request) -> httpx.Response:
        key = request.url.path
        if status and key in status:
            return httpx.Response(status[key], headers=headers or {})
        if key not in routes:
            return httpx.Response(404)
        body = routes[key]
        if isinstance(body, (bytes, str)):
            return httpx.Response(200, content=body)
        return httpx.Response(200, json=body)
    return httpx.Client(transport=httpx.MockTransport(handler))


def item(path, type_="file", size=10):
    name = path.rsplit("/", 1)[-1]
    return {"name": name, "path": path, "type": type_, "size": size,
            "download_url": f"https://raw.githubusercontent.com/acme/skills/main/{path}"}


API = "/repos/acme/skills/contents"
RAW = "/acme/skills/main"


def test_walks_folders_and_makes_paths_relative():
    client = fake_github({
        f"{API}/pdf": [item("pdf/SKILL.md"), item("pdf/scripts", "dir")],
        f"{API}/pdf/scripts": [item("pdf/scripts/run.py")],
        f"{RAW}/pdf/SKILL.md": "---\nname: pdf\ndescription: read pdfs\n---\n",
        f"{RAW}/pdf/scripts/run.py": "print('hi')",
    })
    bundle = load_github("https://github.com/acme/skills/tree/main/pdf", client=client)
    assert [f.path for f in bundle.files] == ["SKILL.md", "scripts/run.py"]
    assert bundle.name == "pdf"
    assert bundle.partial_input is False


def test_large_files_are_not_downloaded():
    client = fake_github({f"{API}/pdf": [item("pdf/SKILL.md"), item("pdf/big.bin", size=10**9)],
                          f"{RAW}/pdf/SKILL.md": "hi"})
    bundle = load_github("https://github.com/acme/skills/tree/main/pdf", client=client)
    assert bundle.files[1].skip_reason == "too_large"


def test_file_cap_stops_the_walk():
    client = fake_github({f"{API}/": [item(f"f{i}.py") for i in range(5)],
                          **{f"{RAW}/f{i}.py": "x" for i in range(5)}})
    bundle = load_github("https://github.com/acme/skills", client=client, max_files=2)
    assert len(bundle.files) == 2
    assert bundle.partial_input is True


def test_blob_url_loads_one_file_as_partial():
    client = fake_github({f"{API}/pdf/SKILL.md": item("pdf/SKILL.md"),
                          f"{RAW}/pdf/SKILL.md": "hi"})
    bundle = load_github("https://github.com/acme/skills/blob/main/pdf/SKILL.md", client=client)
    assert [f.path for f in bundle.files] == ["SKILL.md"]
    assert bundle.partial_input is True


def test_not_found_and_rate_limit_give_clear_errors():
    with pytest.raises(LoaderError, match="GITHUB_TOKEN"):
        load_github("https://github.com/acme/skills/tree/main/nope", client=fake_github({}))

    limited = fake_github({}, status={f"{API}/": 403}, headers={"x-ratelimit-remaining": "0"})
    with pytest.raises(LoaderError, match="rate limit"):
        load_github("https://github.com/acme/skills", client=limited)
