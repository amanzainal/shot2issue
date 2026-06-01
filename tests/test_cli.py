"""End-to-end tests for the CLI mock path and output formats."""

import json

from shot2issue.cli import run


def test_cli_mock_markdown(sample_image, capsys):
    code = run([str(sample_image), "--mock"])
    out = capsys.readouterr().out
    assert code == 0
    assert out.startswith("# ")
    assert "## Steps to Reproduce" in out


def test_cli_mock_json(sample_image, capsys):
    code = run([str(sample_image), "--mock", "--format", "json"])
    out = capsys.readouterr().out
    assert code == 0
    data = json.loads(out)
    assert data["title"]
    assert isinstance(data["repro_steps"], list)
    assert isinstance(data["labels"], list)


def test_cli_missing_image_returns_error(tmp_path, capsys):
    code = run([str(tmp_path / "nope.png"), "--mock"])
    err = capsys.readouterr().err
    assert code == 2
    assert "image not found" in err


def test_cli_make_sample(tmp_path, capsys):
    target = tmp_path / "generated.png"
    code = run(["--make-sample", str(target)])
    out = capsys.readouterr().out
    assert code == 0
    assert target.is_file()
    assert "Wrote synthetic sample screenshot" in out


def test_cli_no_image_without_make_sample_errors(capsys):
    # argparse error() exits with code 2.
    try:
        run(["--mock"])
    except SystemExit as exc:
        assert exc.code == 2
    else:  # pragma: no cover - should not reach
        raise AssertionError("expected SystemExit")


def test_cli_create_without_gh_falls_back(sample_image, capsys, monkeypatch):
    import shot2issue.cli as cli_mod

    monkeypatch.setattr(cli_mod, "gh_available", lambda: False)
    code = run([str(sample_image), "--mock", "--create"])
    captured = capsys.readouterr()
    assert code == 2
    assert "requires the 'gh' CLI" in captured.err
    # Falls back to printing the Markdown issue.
    assert captured.out.startswith("# ")
