"""The prompt sent to the vision LLM.

Kept in one place so every backend asks the model for the exact same JSON
shape that :mod:`shot2issue.schema` knows how to parse.
"""

SYSTEM_PROMPT = (
    "You are a senior software engineer triaging bug reports. You will be "
    "shown a screenshot that captures a software bug (an error message, a "
    "broken UI, a stack trace, etc). Produce a single, well-structured GitHub "
    "issue describing the bug."
)

# The model must reply with ONLY this JSON object (no prose, no markdown fence).
USER_PROMPT = """\
Analyze the attached screenshot and return a GitHub issue as a single JSON
object with exactly these keys:

  - "title":       a concise one-line summary of the bug.
  - "description":  one short paragraph describing what the screenshot shows.
  - "repro_steps":  an ordered list of strings, the steps to reproduce.
  - "expected":     one sentence: what the user expected to happen.
  - "actual":       one sentence: what actually happened (the visible error).
  - "labels":       a list of short GitHub label strings (e.g. "bug", "ui",
                    "crash", "regression").

Reply with ONLY the JSON object and nothing else.
"""


def build_messages() -> dict[str, str]:
    """Return the system + user prompt text for the active backend to use."""
    return {"system": SYSTEM_PROMPT, "user": USER_PROMPT}
