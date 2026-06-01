"""Tests for Markdown rendering of structured issues."""

from shot2issue.render import render_markdown
from shot2issue.schema import Issue


def _full_issue() -> Issue:
    return Issue(
        title="App crashes on save",
        description="An error dialog appears when clicking Save.",
        repro_steps=["Open Settings", "Edit a field", "Click Save"],
        expected="Settings are saved.",
        actual="A NullReferenceException is thrown.",
        labels=["bug", "crash"],
    )


def test_render_has_title_as_h1():
    md = render_markdown(_full_issue())
    assert md.startswith("# App crashes on save\n")


def test_render_includes_all_sections():
    md = render_markdown(_full_issue())
    assert "## Description" in md
    assert "## Steps to Reproduce" in md
    assert "## Expected Behavior" in md
    assert "## Actual Behavior" in md
    assert "## Suggested Labels" in md


def test_render_numbers_repro_steps():
    md = render_markdown(_full_issue())
    assert "1. Open Settings" in md
    assert "2. Edit a field" in md
    assert "3. Click Save" in md


def test_render_labels_as_inline_code():
    md = render_markdown(_full_issue())
    assert "`bug` `crash`" in md


def test_render_omits_empty_optional_sections():
    issue = Issue(title="t", description="d")
    md = render_markdown(issue)
    assert "## Description" in md
    assert "## Steps to Reproduce" not in md
    assert "## Expected Behavior" not in md
    assert "## Actual Behavior" not in md
    assert "## Suggested Labels" not in md


def test_render_ends_with_single_newline():
    md = render_markdown(_full_issue())
    assert md.endswith("\n")
    assert not md.endswith("\n\n")
