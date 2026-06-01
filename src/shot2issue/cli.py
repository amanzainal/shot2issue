"""Command-line interface for shot2issue.

    shot2issue bug.png [--repo owner/name] [--mock] [--create] ...

The image is sent to a pluggable vision LLM, the structured issue is parsed,
and the result is printed as Markdown (or JSON) - or filed via ``gh``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

from shot2issue import __version__
from shot2issue.backends import BackendError, select_backend
from shot2issue.github import GitHubError, create_issue, gh_available
from shot2issue.render import render_markdown
from shot2issue.sample import generate_sample
from shot2issue.schema import Issue, IssueParseError


def build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="shot2issue",
        description=(
            "Drop a screenshot of a bug; get a structured GitHub issue with "
            "repro steps and suggested labels."
        ),
    )
    parser.add_argument(
        "image",
        nargs="?",
        help="path to the bug screenshot (PNG/JPG). Omit when using --make-sample.",
    )
    parser.add_argument(
        "--repo",
        metavar="OWNER/NAME",
        help="target GitHub repository for --create (e.g. octocat/hello-world).",
    )
    parser.add_argument(
        "--backend",
        choices=["mock", "anthropic", "openai"],
        help="force a specific vision backend (default: auto-detect from env).",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="use the canned mock backend (no API key or network needed).",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="output format for the structured issue (default: markdown).",
    )
    parser.add_argument(
        "--create",
        action="store_true",
        help="file the issue on GitHub via `gh issue create` (requires gh).",
    )
    parser.add_argument(
        "--make-sample",
        metavar="PATH",
        help="generate a synthetic sample screenshot at PATH and exit.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"shot2issue {__version__}",
    )
    return parser


def _run_make_sample(path: str) -> int:
    out = generate_sample(path)
    print(f"Wrote synthetic sample screenshot to {out}")
    return 0


def _emit(issue: Issue, fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(issue.to_dict(), indent=2))
    else:
        print(render_markdown(issue), end="")


def run(argv: Optional[Sequence[str]] = None) -> int:
    """Execute the CLI. Returns a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.make_sample:
        return _run_make_sample(args.make_sample)

    if not args.image:
        parser.error("the 'image' argument is required (or use --make-sample)")

    if not Path(args.image).is_file():
        print(f"error: image not found: {args.image}", file=sys.stderr)
        return 2

    # 1. Pick a backend and get raw model output.
    try:
        backend_name, backend = select_backend(mock=args.mock, name=args.backend)
        raw = backend(args.image)
    except BackendError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    # 2. Parse into a structured Issue.
    try:
        issue = Issue.from_model_output(raw)
    except IssueParseError as exc:
        print(f"error: could not parse a structured issue: {exc}", file=sys.stderr)
        return 1

    # 3. Either file it or print it.
    if args.create:
        if not gh_available():
            print(
                "error: --create requires the 'gh' CLI; printing Markdown instead\n",
                file=sys.stderr,
            )
            _emit(issue, "markdown")
            return 2
        try:
            url = create_issue(issue, repo=args.repo)
        except GitHubError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"Created issue: {url}")
        return 0

    if backend_name == "mock":
        print("# (generated with --mock backend)\n", file=sys.stderr)
    _emit(issue, args.format)
    return 0


def main() -> None:
    """Console-script entry point."""
    raise SystemExit(run())


if __name__ == "__main__":
    main()
