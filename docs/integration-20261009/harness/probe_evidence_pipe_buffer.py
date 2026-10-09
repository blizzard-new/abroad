"""Diagnose the inherited test's readline/communicate buffering, without app edits."""
import json
import os
from pathlib import Path
import subprocess
import sys

program = r'''
import os, sys
os.set_blocking(sys.stdout.fileno(), False)
while True:
    try: os.write(sys.stdout.fileno(), b'x' * 4096)
    except BlockingIOError: break
print('PIPE_FULL', file=sys.stderr, flush=True)
print('WEB_CASE synthetic::failure call failed', flush=True)
print('ORIGINAL:' + 'y' * 262144 + ':END', flush=True)
'''
env = {k: v for k, v in os.environ.items() if k != 'PYTHONUNBUFFERED'}
results = []
for bufsize in (-1, 0):
    for iteration in range(3):
        process = subprocess.Popen([sys.executable, '-c', program], stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, env=env, bufsize=bufsize)
        # The child is nonblocking and reaches its real failure with no reader.
        # This deterministically models a parent scheduled after the child exits.
        process.wait(timeout=10)
        marker = process.stderr.readline()
        output, error = process.communicate(timeout=10)
        row = {'bufsize': bufsize, 'iteration': iteration, 'returncode': process.returncode,
               'marker': marker.decode(), 'stderr_bytes_returned_by_communicate': len(error),
               'actual_blocking_error_retained': b'BlockingIOError' in error}
        assert process.returncode != 0 and marker == b'PIPE_FULL\n'
        assert row['actual_blocking_error_retained'] == (bufsize == 0), row
        results.append(row)
result = {'status': 'passed', 'cases': results,
          'root_cause': 'Buffered stderr.readline can prefetch the traceback. communicate then reads the OS descriptor and misses buffered bytes. An unbuffered pipe preserves the same actual child failure.',
          'application_changes': False, 'test_file_changes': False}
Path('/workspace/integration-evidence/memory-pipe-buffer-proof.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
