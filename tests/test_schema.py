"""Tests for the Issue schema and tolerant model-output parsing."""

import pytest

from shot2issue.schema import Issue, IssueParseError


def test_from_dict_minimal_required_fields():
    issue = Issue.from_dict({"title": "Boom", "description": "It broke."})
    assert issue.title == "Boom"
    assert issue.description == "It broke."
    assert issue.repro_steps == []
    assert issue.labels == []
    assert issue.expected == ""
    assert issue.actual == ""


def test_from_dict_full():
    issue = Issue.from_dict(
        {
            "title": "Crash on save",
            "description": "An error dialog appears.",
            "repro_steps": ["Open app", "Click save"],
            "expected": "It saves.",
            "actual": "It crashes.",
            "labels": ["bug", "crash"],
        }
    )
    assert issue.repro_steps == ["Open app", "Click save"]
    assert issue.labels == ["bug", "crash"]
    assert issue.expected == "It saves."


@pytest.mark.parametrize("missing", ["title", "description"])
def test_from_dict_missing_required_raises(missing):
    data = {"title": "t", "description": "d"}
    del data[missing]
    with pytest.raises(IssueParseError):
        Issue.from_dict(data)


def test_from_dict_empty_required_raises():
    with pytest.raises(IssueParseError):
        Issue.from_dict({"title": "   ", "description": "d"})


def test_from_dict_coerces_string_repro_steps():
    # A model that returns a newline-joined string instead of a list.
    issue = Issue.from_dict(
        {"title": "t", "description": "d", "repro_steps": "Step one\nStep two"}
    )
    assert issue.repro_steps == ["Step one", "Step two"]


def test_from_dict_filters_blank_labels():
    issue = Issue.from_dict(
        {"title": "t", "description": "d", "labels": ["bug", "", None, "ui"]}
    )
    assert issue.labels == ["bug", "ui"]


def test_from_dict_strips_whitespace_and_handles_null_text():
    issue = Issue.from_dict(
        {"title": "  t  ", "description": "d", "expected": None}
    )
    assert issue.title == "t"
    assert issue.expected == ""


def test_from_dict_non_dict_raises():
    with pytest.raises(IssueParseError):
        Issue.from_dict(["not", "a", "dict"])  # type: ignore[arg-type]


def test_to_dict_roundtrip():
    data = {
        "title": "t",
        "description": "d",
        "repro_steps": ["a", "b"],
        "expected": "e",
        "actual": "a",
        "labels": ["bug"],
    }
    assert Issue.from_dict(data).to_dict() == data


def test_from_model_output_bare_json():
    raw = '{"title": "t", "description": "d"}'
    issue = Issue.from_model_output(raw)
    assert issue.title == "t"


def test_from_model_output_fenced_json():
    raw = "Here is your issue:\n```json\n{\"title\": \"t\", \"description\": \"d\"}\n```\nThanks!"
    issue = Issue.from_model_output(raw)
    assert issue.description == "d"


def test_from_model_output_json_embedded_in_prose():
    raw = 'Sure! {"title": "t", "description": "d", "labels": ["bug"]} Hope that helps.'
    issue = Issue.from_model_output(raw)
    assert issue.labels == ["bug"]


def test_from_model_output_empty_raises():
    with pytest.raises(IssueParseError):
        Issue.from_model_output("   ")


def test_from_model_output_no_json_raises():
    with pytest.raises(IssueParseError):
        Issue.from_model_output("there is no json here at all")
