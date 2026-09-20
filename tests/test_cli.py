from typer.testing import CliRunner

from reqforge.cli.commands import app

runner = CliRunner()


def test_help_lists_core_commands():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in ["targets", "import", "create-request", "replay", "mutate", "compare", "test", "evidence", "scope"]:
        assert command in result.stdout


def test_targets_returns_empty_message_for_unknown_domain():
    result = runner.invoke(app, ["targets", "example.com"])
    assert result.exit_code == 0
    assert "No endpoints found for domain: example.com" in result.stdout


def test_targets_lists_imported_subdomains_for_parent_domain():
    result = runner.invoke(app, ["import", "reconforge-export.json"])
    assert result.exit_code == 0
    result2 = runner.invoke(app, ["targets", "facebook.com"])
    assert result2.exit_code == 0
    assert "https://www.facebook.com/login/" in result2.stdout
