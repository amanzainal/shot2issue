"""File issues on GitHub via the ``gh`` CLI.

We shell out to ``gh issue create`` rather than re-implementing auth, so the
user's existing ``gh`` login is reused and no token is handled by this tool.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from shot2issue.render import render_markdown
from shot2issue.schema import Issue


class GitHubError(RuntimeError):
    """Raised when an issue cannot be filed via ``gh``."""


def gh_available() -> bool:
    """Return True if the ``gh`` CLI is on PATH."""
    return shutil.which("gh") is not None


def build_gh_command(issue: Issue, body_file: str, repo: Optional[str]) -> list[str]:
    """Construct the ``gh issue create`` argv for ``issue``.

    Split out from :func:`create_issue` so it can be unit-tested without
    invoking ``gh``.
    """
    cmd = ["gh", "issue", "create", "--title", issue.title, "--body-file", body_file]
    if repo:
        cmd += ["--repo", repo]
    for label in issue.labels:
        cmd += ["--label", label]
    return cmd


def create_issue(issue: Issue, repo: Optional[str] = None) -> str:
    """File ``issue`` via ``gh issue create`` and return the new issue URL.

    Raises:
        GitHubError: if ``gh`` is missing or the command fails.
    """
    if not gh_available():
        raise GitHubError("the 'gh' CLI is not installed or not on PATH")

    body = render_markdown(issue)
    tmp = Path(tempfile.mkdtemp(prefix="shot2issue-")) / "issue-body.md"
    tmp.write_text(body, encoding="utf-8")
    cmd = build_gh_command(issue, str(tmp), repo)

    try:
        result = subprocess.run(  # noqa: S603 (argv list, no shell)
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        # Best-effort cleanup of the temp body file.
        try:
            tmp.unlink()
            tmp.parent.rmdir()
        except OSError:
            pass

    if result.returncode != 0:
        raise GitHubError(
            f"`gh issue create` failed (exit {result.returncode}): "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    return result.stdout.strip()
