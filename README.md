# shot2issue

> Drop a screenshot of a bug; get a structured GitHub issue with repro steps and labels.

`shot2issue` takes a screenshot of a bug (an error dialog, a broken UI, a stack
trace) and turns it into a clean, structured GitHub issue — title, description,
steps to reproduce, expected/actual behavior, and suggested labels — using a
pluggable vision LLM. Print it as Markdown, dump it as JSON, or file it straight
to GitHub with `gh`.

## Why it exists

Good bug reports take effort: a clear title, repro steps, and the right labels.
In practice people paste a screenshot into a chat and move on. `shot2issue`
closes that gap — point it at the screenshot you already have and it drafts a
proper issue for you. The vision backend is pluggable (Anthropic or OpenAI via
an env key), and a built-in `--mock` mode runs the whole pipeline with no key
and no network, so it is trivial to try and easy to test.

## Install

Requires Python 3.11+. This project uses [uv](https://docs.astral.sh/uv/).

```bash
# from a clone of this repo
uv sync

# run the CLI through uv
uv run shot2issue --version
```

To use a real vision backend, copy the example env and set one key:

```bash
cp .env.example .env
# then edit .env and set ANTHROPIC_API_KEY or OPENAI_API_KEY
```

Keys are read from the environment only — nothing is ever hardcoded. The
optional Anthropic/OpenAI SDKs are installed on demand (`pip install anthropic`
or `pip install openai`); the `--mock` path needs neither.

## Usage

```text
shot2issue [IMAGE] [--repo OWNER/NAME] [--backend {mock,anthropic,openai}]
           [--mock] [--format {markdown,json}] [--create]
           [--make-sample PATH]
```

### Try it with no API key (mock mode)

Generate a synthetic sample screenshot, then run the mock pipeline:

```bash
uv run shot2issue --make-sample sample.png
uv run shot2issue sample.png --mock
```

Sample output (Markdown):

```markdown
# App crashes with NullReferenceException on Save

## Description
The screenshot shows an unhandled error dialog appearing when the user clicks
the Save button on the settings page. A red banner reads 'Something went wrong'
above a stack trace.

## Steps to Reproduce
1. Open the application and navigate to Settings
2. Change any field in the General tab
3. Click the Save button

## Expected Behavior
The settings are saved and a success toast is shown.

## Actual Behavior
An error dialog appears with a NullReferenceException and the settings are not saved.

## Suggested Labels
`bug` `crash` `settings`
```

### JSON output

```bash
uv run shot2issue sample.png --mock --format json
```

### Against a real screenshot with a vision LLM

```bash
# auto-detects the backend from whichever key is set in your environment
uv run shot2issue bug.png

# or force one
uv run shot2issue bug.png --backend openai
```

### File it directly on GitHub

With the [`gh`](https://cli.github.com/) CLI installed and authenticated:

```bash
uv run shot2issue bug.png --repo octocat/hello-world --create
```

This renders the Markdown body, passes each suggested label through, and runs
`gh issue create` for you. If `gh` is not available, `shot2issue` prints the
Markdown instead so you can paste it yourself.

## How it works

1. **Capture the prompt contract.** `shot2issue` asks the vision model for a
   single JSON object with a fixed set of keys (`title`, `description`,
   `repro_steps`, `expected`, `actual`, `labels`). The prompt lives in one
   place so every backend asks for the exact same shape.
2. **Send the image to a pluggable backend.** `mock`, `anthropic`, and `openai`
   backends are registered by name; selection is driven by `--mock`,
   `--backend`, `SHOT2ISSUE_BACKEND`, or an available provider key — in that
   order.
3. **Parse tolerantly.** Model output is parsed into an `Issue` dataclass even
   when the JSON is wrapped in a ```` ```json ```` fence or surrounded by prose.
   Types are normalized (a newline-joined string becomes a list, blank labels
   are dropped) and required fields are validated.
4. **Render or file.** The `Issue` is rendered to GitHub-flavored Markdown (or
   JSON), or filed via `gh issue create`.

```
screenshot ──▶ backend (vision LLM) ──▶ raw JSON-ish text
                                              │
                                  Issue.from_model_output()
                                              │
                              ┌───────────────┴───────────────┐
                        render_markdown()                gh issue create
```

## Development

```bash
uv sync
uv run pytest -q
```

The test suite covers schema parsing, Markdown rendering, backend selection,
and the full mock CLI path — no API key or network required.

## Roadmap

- Redaction pass to blur secrets/PII detected in the screenshot before upload.
- A local OCR fallback backend (no cloud) for offline triage.
- De-duplication against existing open issues before filing.
- Support for attaching the original screenshot to the created issue.
- Config file for default repo, labels, and backend.

## License

MIT — see [LICENSE](./LICENSE). Copyright (c) 2026 The Authors.
