"""shot2issue: screenshot of a bug to a structured GitHub issue.

Drop a screenshot of a bug; get a structured GitHub issue with repro steps
and suggested labels. The vision LLM backend is pluggable via environment
variables, and a ``--mock`` path makes the whole pipeline testable without a
key or network.
"""

from shot2issue.schema import Issue

__version__ = "0.1.0"

__all__ = ["Issue", "__version__"]
