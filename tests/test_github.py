"""Tests for the gh command builder (no gh invocation)."""

from shot2issue.github import build_gh_command
from shot2issue.schema import Issue


def _issue() -> Issue:
    return Issue(
        title="Crash on save",
        description="It crashes.",
        labels=["bug", "crash"],
    )


def test_build_gh_command_basic():
    cmd = build_gh_command(_issue(), "/tmp/body.md", repo=None)
    assert cmd[:3] == ["gh", "issue", "create"]
    assert "--title" in cmd
    assert "Crash on save" in cmd
    assert "--body-file" in cmd
    assert "/tmp/body.md" in cmd
    assert "--repo" not in cmd


def test_build_gh_command_with_repo_and_labels():
    cmd = build_gh_command(_issue(), "/tmp/body.md", repo="octocat/hello-world")
    assert "--repo" in cmd
    assert "octocat/hello-world" in cmd
    # Each label is passed as its own --label flag.
    assert cmd.count("--label") == 2
    assert "bug" in cmd
    assert "crash" in cmd
