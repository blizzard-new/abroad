import json,sys,pytest
from pathlib import Path
cases=json.loads(Path("/workspace/integration-evidence/six-browser-failed-nodeids.json").read_text())
raise SystemExit(pytest.main(["-q","--tb=short",*cases,"--junitxml=/workspace/integration-evidence/six-browser-failures-fixed/results.xml"]))
