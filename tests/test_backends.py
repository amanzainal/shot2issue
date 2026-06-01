"""Tests for backend selection and the mock backend (no network/keys)."""

import pytest

from shot2issue.backends import (
    BackendError,
    load_fixture_text,
    mock_backend,
    select_backend,
)
from shot2issue.schema import Issue


def test_mock_backend_returns_parseable_fixture(sample_image):
    raw = mock_backend(str(sample_image))
    issue = Issue.from_model_output(raw)
    assert issue.title
    assert issue.labels  # the fixture ships labels


def test_mock_backend_missing_image_raises(tmp_path):
    with pytest.raises(BackendError):
        mock_backend(str(tmp_path / "does-not-exist.png"))


def test_load_fixture_text_is_valid_issue():
    issue = Issue.from_model_output(load_fixture_text())
    assert issue.title == "App crashes with NullReferenceException on Save"


def test_select_backend_mock_flag_wins(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "should-be-ignored")
    name, backend = select_backend(mock=True)
    assert name == "mock"
    assert backend is mock_backend


def test_select_backend_explicit_name(monkeypatch):
    monkeypatch.delenv("SHOT2ISSUE_BACKEND", raising=False)
    name, _ = select_backend(name="mock")
    assert name == "mock"


def test_select_backend_unknown_name_raises():
    with pytest.raises(BackendError):
        select_backend(name="nope")


def test_select_backend_env_var(monkeypatch):
    monkeypatch.setenv("SHOT2ISSUE_BACKEND", "mock")
    name, _ = select_backend()
    assert name == "mock"


def test_select_backend_prefers_anthropic_key(monkeypatch):
    monkeypatch.delenv("SHOT2ISSUE_BACKEND", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    name, _ = select_backend()
    assert name == "anthropic"


def test_select_backend_falls_back_to_openai(monkeypatch):
    monkeypatch.delenv("SHOT2ISSUE_BACKEND", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    name, _ = select_backend()
    assert name == "openai"


def test_select_backend_no_config_raises(monkeypatch):
    monkeypatch.delenv("SHOT2ISSUE_BACKEND", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(BackendError):
        select_backend()
