"""Structured issue schema and parsing.

The vision LLM is asked to return a single JSON object describing a bug
report. This module defines the canonical shape of that object as a small,
dependency-free dataclass and provides robust parsing from raw model output
(which is often JSON wrapped in prose or a ```json fence).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

# Fields the model is asked to produce. Kept here so the prompt and the parser
# never drift apart.
REQUIRED_FIELDS = ("title", "description")
LIST_FIELDS = ("repro_steps", "labels")
TEXT_FIELDS = ("title", "description", "expected", "actual")


class IssueParseError(ValueError):
    """Raised when raw model output cannot be parsed into an :class:`Issue`."""


@dataclass
class Issue:
    """A structured bug report extracted from a screenshot.

    Attributes:
        title: One-line summary of the bug.
        description: A short paragraph describing what is shown in the screenshot.
        repro_steps: Ordered steps to reproduce the bug.
        expected: What the user expected to happen.
        actual: What actually happened (often the error in the screenshot).
        labels: Suggested GitHub labels (e.g. ``bug``, ``ui``, ``crash``).
    """

    title: str
    description: str
    repro_steps: list[str] = field(default_factory=list)
    expected: str = ""
    actual: str = ""
    labels: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return a plain JSON-serializable dict of this issue."""
        return {
            "title": self.title,
            "description": self.description,
            "repro_steps": list(self.repro_steps),
            "expected": self.expected,
            "actual": self.actual,
            "labels": list(self.labels),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Issue":
        """Build an :class:`Issue` from a dict, validating and normalizing types.

        Raises:
            IssueParseError: if required fields are missing or empty.
        """
        if not isinstance(data, dict):
            raise IssueParseError(f"expected a JSON object, got {type(data).__name__}")

        normalized: dict[str, Any] = {}

        for key in TEXT_FIELDS:
            value = data.get(key, "")
            if value is None:
                value = ""
            normalized[key] = str(value).strip()

        for key in LIST_FIELDS:
            normalized[key] = _coerce_str_list(data.get(key))

        for key in REQUIRED_FIELDS:
            if not normalized.get(key):
                raise IssueParseError(f"missing required field: {key!r}")

        return cls(**normalized)

    @classmethod
    def from_model_output(cls, raw: str) -> "Issue":
        """Parse raw vision-model text into an :class:`Issue`.

        Tolerates a bare JSON object, a ```json fenced block, or JSON embedded
        in surrounding prose.

        Raises:
            IssueParseError: if no parseable JSON object can be found.
        """
        data = _extract_json_object(raw)
        return cls.from_dict(data)


def _coerce_str_list(value: Any) -> list[str]:
    """Coerce an arbitrary value into a clean list of non-empty strings."""
    if value is None:
        return []
    if isinstance(value, str):
        # Allow newline- or comma-separated strings as a fallback.
        parts = re.split(r"[\n,]+", value)
        return [p.strip(" -\t") for p in parts if p.strip(" -\t")]
    if isinstance(value, (list, tuple)):
        out: list[str] = []
        for item in value:
            if item is None:
                continue
            text = str(item).strip()
            if text:
                out.append(text)
        return out
    return [str(value).strip()]


def _extract_json_object(raw: str) -> dict[str, Any]:
    """Find and parse the first JSON object in ``raw``."""
    if raw is None:
        raise IssueParseError("model returned no output")
    text = raw.strip()
    if not text:
        raise IssueParseError("model returned empty output")

    # 1. Try a fenced ```json ... ``` block first.
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        candidate = fence.group(1)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass  # fall through to other strategies

    # 2. Try the whole string as JSON.
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 3. Try the substring from the first '{' to the last '}'.
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise IssueParseError(f"could not parse JSON from model output: {exc}") from exc

    raise IssueParseError("no JSON object found in model output")
