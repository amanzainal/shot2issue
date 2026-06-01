"""Pluggable vision-LLM backends.

A backend takes an image path and returns raw model text (expected to contain
the JSON object described in :mod:`shot2issue.prompt`). Three backends ship:

* ``mock``      - returns a canned fixture; no key or network needed.
* ``anthropic`` - Anthropic Messages API (Claude vision).
* ``openai``    - OpenAI Chat Completions API (GPT vision).

Backend selection is driven by environment variables so keys are never
hardcoded. See :func:`select_backend`.
"""

from __future__ import annotations

import base64
import importlib.resources as resources
import mimetypes
import os
from pathlib import Path
from typing import Callable, Optional

from shot2issue.prompt import build_messages

# A backend is just a callable: (image_path) -> raw model text.
Backend = Callable[[str], str]

# Default model ids per provider; override with SHOT2ISSUE_MODEL.
DEFAULT_ANTHROPIC_MODEL = "claude-3-5-sonnet-latest"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


class BackendError(RuntimeError):
    """Raised when a backend cannot be constructed or run."""


def _read_image_b64(image_path: str) -> tuple[str, str]:
    """Return ``(media_type, base64_data)`` for ``image_path``."""
    path = Path(image_path)
    if not path.is_file():
        raise BackendError(f"image not found: {image_path}")
    media_type, _ = mimetypes.guess_type(str(path))
    if media_type is None:
        media_type = "image/png"
    data = base64.standard_b64encode(path.read_bytes()).decode("ascii")
    return media_type, data


def mock_backend(image_path: str) -> str:
    """Return the canned fixture issue as JSON text.

    The image is still validated to exist so the mock path exercises the same
    "is this a real file" failure mode as the live backends.
    """
    if not Path(image_path).is_file():
        raise BackendError(f"image not found: {image_path}")
    return load_fixture_text()


def load_fixture_text() -> str:
    """Load the canned mock issue JSON shipped inside the package."""
    return (
        resources.files("shot2issue.fixtures")
        .joinpath("mock_issue.json")
        .read_text(encoding="utf-8")
    )


def anthropic_backend(image_path: str) -> str:
    """Call the Anthropic Messages API with the screenshot attached."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise BackendError("ANTHROPIC_API_KEY is not set")
    try:
        import anthropic  # noqa: WPS433 (lazy import: optional dependency)
    except ImportError as exc:  # pragma: no cover - depends on optional dep
        raise BackendError(
            "the 'anthropic' package is required for the anthropic backend "
            "(pip install anthropic)"
        ) from exc

    media_type, data = _read_image_b64(image_path)
    model = os.environ.get("SHOT2ISSUE_MODEL", DEFAULT_ANTHROPIC_MODEL)
    prompts = build_messages()

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(  # pragma: no cover - network call
        model=model,
        max_tokens=1024,
        system=prompts["system"],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": data,
                        },
                    },
                    {"type": "text", "text": prompts["user"]},
                ],
            }
        ],
    )
    return "".join(
        block.text for block in response.content if getattr(block, "type", "") == "text"
    )


def openai_backend(image_path: str) -> str:
    """Call the OpenAI Chat Completions API with the screenshot attached."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise BackendError("OPENAI_API_KEY is not set")
    try:
        import openai  # noqa: WPS433 (lazy import: optional dependency)
    except ImportError as exc:  # pragma: no cover - depends on optional dep
        raise BackendError(
            "the 'openai' package is required for the openai backend "
            "(pip install openai)"
        ) from exc

    media_type, data = _read_image_b64(image_path)
    model = os.environ.get("SHOT2ISSUE_MODEL", DEFAULT_OPENAI_MODEL)
    prompts = build_messages()
    data_url = f"data:{media_type};base64,{data}"

    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(  # pragma: no cover - network call
        model=model,
        messages=[
            {"role": "system", "content": prompts["system"]},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompts["user"]},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ],
    )
    return response.choices[0].message.content or ""


# Registry of named backends. ``mock`` is always available; the others require
# their SDK + key at call time.
BACKENDS: dict[str, Backend] = {
    "mock": mock_backend,
    "anthropic": anthropic_backend,
    "openai": openai_backend,
}


def select_backend(mock: bool = False, name: Optional[str] = None) -> tuple[str, Backend]:
    """Pick a backend and return ``(name, callable)``.

    Resolution order:
    1. ``mock=True``               -> the mock backend.
    2. explicit ``name``           -> that backend (must be registered).
    3. ``SHOT2ISSUE_BACKEND`` env  -> that backend.
    4. an available provider key   -> anthropic, then openai.

    Raises:
        BackendError: if no backend can be resolved.
    """
    if mock:
        return "mock", BACKENDS["mock"]

    chosen = name or os.environ.get("SHOT2ISSUE_BACKEND")
    if chosen:
        chosen = chosen.lower()
        if chosen not in BACKENDS:
            raise BackendError(
                f"unknown backend {chosen!r}; choices: {', '.join(sorted(BACKENDS))}"
            )
        return chosen, BACKENDS[chosen]

    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic", BACKENDS["anthropic"]
    if os.environ.get("OPENAI_API_KEY"):
        return "openai", BACKENDS["openai"]

    raise BackendError(
        "no vision backend configured: set ANTHROPIC_API_KEY or OPENAI_API_KEY, "
        "or pass --mock to run without a key"
    )
