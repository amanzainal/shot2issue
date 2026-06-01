"""Render a structured :class:`~shot2issue.schema.Issue` as GitHub Markdown."""

from __future__ import annotations

from shot2issue.schema import Issue


def render_markdown(issue: Issue) -> str:
    """Render ``issue`` as a Markdown GitHub-issue body.

    The title becomes an H1, sections are H2s, repro steps are an ordered
    list, and labels are rendered as inline code at the bottom. Empty optional
    sections are omitted so the output stays clean.
    """
    lines: list[str] = []
    lines.append(f"# {issue.title}")
    lines.append("")
    lines.append("## Description")
    lines.append(issue.description)
    lines.append("")

    if issue.repro_steps:
        lines.append("## Steps to Reproduce")
        for i, step in enumerate(issue.repro_steps, start=1):
            lines.append(f"{i}. {step}")
        lines.append("")

    if issue.expected:
        lines.append("## Expected Behavior")
        lines.append(issue.expected)
        lines.append("")

    if issue.actual:
        lines.append("## Actual Behavior")
        lines.append(issue.actual)
        lines.append("")

    if issue.labels:
        rendered = " ".join(f"`{label}`" for label in issue.labels)
        lines.append("## Suggested Labels")
        lines.append(rendered)
        lines.append("")

    # Collapse the trailing blank line into a single newline-terminated doc.
    return "\n".join(lines).rstrip() + "\n"
