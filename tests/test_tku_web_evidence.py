"""Reproduce the filled nonblocking CI pipe that interrupted real pytest."""
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("repair", [False, True])
def test_evidence_output_preserves_a_long_failure_on_a_full_pipe(repair):
    script = Path(__file__).resolve().parents[1] / "scripts/run_web_quality_tests.py"
    program = f"""
import importlib.util, os, sys
from types import SimpleNamespace
spec = importlib.util.spec_from_file_location('web_runner', {str(script)!r})
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
os.set_blocking(sys.stdout.fileno(), False)
while True:
    try: os.write(sys.stdout.fileno(), b'x' * 4096)
    except BlockingIOError: break
print('PIPE_FULL', file=sys.stderr, flush=True)
if {repair!r}: module.use_blocking_output()
module.Progress().pytest_runtest_logreport(SimpleNamespace(
    when='call', failed=True, skipped=False, nodeid='synthetic::failure',
    outcome='failed', duration=0.001, longrepr='ORIGINAL:' + 'y' * 262144 + ':END'))
"""
    process = subprocess.Popen([sys.executable, "-c", program], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert process.stderr.readline() == b"PIPE_FULL\n"
    if not repair:
        # Keep the reader stopped until the original logger reaches EAGAIN.
        process.wait(timeout=10)
    output, error = process.communicate(timeout=30)
    if repair:
        assert process.returncode == 0, error.decode()
        assert output.endswith(b"ORIGINAL:" + b"y" * 262144 + b":END\n")
        assert b"WEB_CASE synthetic::failure call failed" in output
    else:
        assert process.returncode != 0
        assert b"BlockingIOError" in error
