from slopstop import __version__, cli


def test_version(capsys):
    assert cli.main(["--version"]) == 0
    assert __version__ in capsys.readouterr().out


def test_no_command_is_usage_error(capsys):
    assert cli.main([]) == 2
