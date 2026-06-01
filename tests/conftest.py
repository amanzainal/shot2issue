"""Shared pytest fixtures."""

from pathlib import Path

import pytest

from shot2issue.sample import generate_sample


@pytest.fixture()
def sample_image(tmp_path) -> Path:
    """Generate a synthetic sample screenshot in a temp dir."""
    return generate_sample(tmp_path / "bug.png")
