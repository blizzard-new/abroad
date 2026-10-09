"""Reproduce the filled nonblocking CI pipe that interrupted real pytest."""
import json
import os
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
report = SimpleNamespace(
    when='call', failed=True, skipped=False, nodeid='synthetic::failure',
    outcome='failed', duration=0.001, longrepr='ORIGINAL:' + 'y' * 262144 + ':END')
if {repair!r}:
    # Reproduce the flag changing after startup, as the original CI did.
    os.set_blocking(sys.stdout.fileno(), False)
    module.Progress().pytest_runtest_logreport(report)
else:
    print(f'WEB_CASE {{report.nodeid}} call failed', flush=True)
    print(str(report.longrepr), flush=True)
"""
    # Reproduce the original buffered logger regardless of the outer test runner.
    environment = {key: value for key, value in os.environ.items() if key != "PYTHONUNBUFFERED"}
    # readline() and communicate() share stderr. A buffered readline can prefetch
    # the traceback, which communicate's descriptor reads then fail to return.
    process = subprocess.Popen([sys.executable, "-c", program], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               env=environment, bufsize=0)
    if not repair:
        # Keep both readers stopped until the original logger reaches EAGAIN.
        # This also exercises the case where the entire traceback is already
        # available before the parent reads the PIPE_FULL marker.
        process.wait(timeout=10)
    assert process.stderr.readline() == b"PIPE_FULL\n"
    output, error = process.communicate(timeout=30)
    if repair:
        assert process.returncode == 0, error.decode()
        assert output.endswith(b"ORIGINAL:" + b"y" * 262144 + b":END\n")
        assert b"WEB_CASE synthetic::failure call failed" in output
    else:
        assert process.returncode != 0
        assert b"BlockingIOError" in error


def test_real_pytest_terminal_flush_survives_flag_change_and_full_pipe(tmp_path):
    """Reproduce the separate terminal.flush failure that Progress alone missed."""
    import xml.etree.ElementTree as ET
    test = tmp_path / "test_synthetic_terminal.py"
    test.write_text("""
import os,sys

def test_first():
    os.set_blocking(sys.__stdout__.fileno(), False)
    raise AssertionError('ORIGINAL:' + 'y' * 262144 + ':END')

def test_tail_failure():
    raise AssertionError('TAIL_FAILURE')

def test_final_pass():
    assert True
""")
    xml = tmp_path / "original.xml"
    command = [str(test), "-vv", "--tb=short", "--capture=tee-sys", f"--junitxml={xml}"]
    program = """
import json,os,sys
from scripts.run_web_quality_tests import stream_pytest
os.set_blocking(sys.stdout.fileno(),False)
while True:
    try:os.write(sys.stdout.fileno(),b'x'*4096)
    except BlockingIOError:break
print('PIPE_FULL',file=sys.stderr,flush=True)
raise SystemExit(stream_pytest(json.loads(sys.argv[1])))
"""
    process = subprocess.Popen([sys.executable, "-c", program, json.dumps(command)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        cwd=Path(__file__).resolve().parents[1], bufsize=0)
    assert process.stderr.readline() == b"PIPE_FULL\n"
    output, error = process.communicate(timeout=30)
    assert process.returncode == 1, error.decode()
    assert b"ORIGINAL:" + b"y" * 262144 + b":END" in output
    assert b"TAIL_FAILURE" in output and b"test_final_pass" in output
    assert b"INTERNALERROR" not in output and b"BlockingIOError" not in output
    cases = list(ET.parse(xml).getroot().iter("testcase"))
    assert len(cases) == 3
    assert sum(c.find("failure") is not None for c in cases) == 2
    assert not any(c.find("error") is not None for c in cases)
