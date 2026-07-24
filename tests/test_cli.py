from exchange_info import cli


class _ReconfigurableStream:
    def __init__(self) -> None:
        self.options: dict[str, str] = {}

    def reconfigure(self, **options: str) -> None:
        self.options = options


def test_cli_configures_utf8_console_output(monkeypatch) -> None:
    stdout = _ReconfigurableStream()
    stderr = _ReconfigurableStream()
    monkeypatch.setattr(cli.sys, "stdout", stdout)
    monkeypatch.setattr(cli.sys, "stderr", stderr)

    cli._configure_console_encoding()

    assert stdout.options == {"encoding": "utf-8", "errors": "replace"}
    assert stderr.options == {"encoding": "utf-8", "errors": "replace"}
