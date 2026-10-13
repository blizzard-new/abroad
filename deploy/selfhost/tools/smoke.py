"""End-to-end checks of the running stack, from inside the app container (where the database address works).

Prints PASS/FAIL lines and exits non-zero if anything failed. It leaves no test data behind: the rows and the stored
object it creates are deleted again at the end.
"""
import json
import os
import sys
import uuid

import requests

APP = "http://127.0.0.1:8000"
BASE = os.environ["EXCHANGE_SUPABASE_URL"].rstrip("/")
KEY = os.environ["EXCHANGE_SUPABASE_SECRET_KEY"]
HEADERS = {"Authorization": "Bearer " + KEY, "apikey": KEY}
EXPECTED_SCHOOLS = 6
failures = []


def check(name, ok, detail=""):
    print(("PASS  " if ok else "FAIL  ") + name + (("  - " + str(detail)) if detail else ""))
    if not ok:
        failures.append(name)


def get(url, **kw):
    return requests.get(url, timeout=60, **kw)


# 1. the web service itself
r = get(APP + "/health")
check("web service answers /health", r.status_code == 200, r.status_code)
for header in ("Content-Security-Policy", "Strict-Transport-Security", "X-Content-Type-Options"):
    check("security header " + header, header in r.headers or header in get(APP + "/").headers)

r = get(APP + "/universities")
names = [u["school_name"] for u in r.json()] if r.status_code == 200 else []
check("all %d schools are listed" % EXPECTED_SCHOOLS, len(names) >= EXPECTED_SCHOOLS, ", ".join(names))
for school in names[:EXPECTED_SCHOOLS]:
    d = get(APP + "/student-dashboard", params={"school": school})
    count = len(d.json().get("partner_universities", [])) if d.status_code == 200 else -1
    check("dashboard for " + school, d.status_code == 200 and count > 0, "%s partner schools" % count)

# 2. the database through its REST door
r = get(BASE + "/rest/v1/exchange_accounts?select=id&limit=1", headers=HEADERS)
check("service key can read the database", r.status_code == 200, r.status_code)
anon_key = os.environ.get("SMOKE_ANON_KEY", "")
if anon_key:
    r = get(BASE + "/rest/v1/exchange_accounts?select=id&limit=1", headers={"Authorization": "Bearer " + anon_key, "apikey": anon_key})
    check("the public (anon) key cannot read accounts", r.status_code in (401, 403) or r.json() == [], r.status_code)
r = get(BASE + "/rest/v1/rpc/rls_auto_enable", headers=HEADERS)
check("internal helper function is not callable through REST", r.status_code in (401, 403, 404), r.status_code)

# 3. a write through the program (feedback form) and back out of the database
marker = "selfhost smoke test " + uuid.uuid4().hex
r = requests.post(APP + "/feedback", json={"kind": "other", "message": marker, "route": "smoke"}, timeout=60)
if r.status_code == 429:
    print("SKIP  feedback write: the form's rate limit was hit by earlier runs (wait 10 minutes)")
else:
    check("feedback form accepts a message", r.status_code in (200, 201, 202), r.status_code)
    rows = get(BASE + "/rest/v1/exchange_user_feedback?select=id,message&message=eq." + marker, headers=HEADERS).json()
    check("the message is in the database", isinstance(rows, list) and len(rows) == 1)
    if rows:
        d = requests.delete(BASE + "/rest/v1/exchange_user_feedback?id=eq." + rows[0]["id"], headers=HEADERS, timeout=60)
        check("test row removed again", d.status_code in (200, 204), d.status_code)

# 4. the private document store
bucket = "exchange-private-vault"
b = get(BASE + "/storage/v1/bucket/" + bucket, headers=HEADERS)
check("private bucket exists", b.status_code == 200, b.status_code)
check("bucket is private", b.status_code == 200 and b.json().get("public") is False)
key = "vault/selftest/" + uuid.uuid4().hex
payload = os.urandom(2048)
up = requests.post(BASE + "/storage/v1/object/%s/%s" % (bucket, key), headers={**HEADERS, "Content-Type": "application/octet-stream", "x-upsert": "false"}, data=payload, timeout=60)
check("a file can be stored", up.status_code == 200, up.status_code)
down = get(BASE + "/storage/v1/object/authenticated/%s/%s" % (bucket, key), headers=HEADERS)
check("the same bytes come back", down.status_code == 200 and down.content == payload)
anon = requests.get(BASE + "/storage/v1/object/public/%s/%s" % (bucket, key), timeout=60)
check("the file is NOT publicly readable", anon.status_code in (400, 401, 403, 404), anon.status_code)
rm = requests.delete(BASE + "/storage/v1/object/" + bucket, headers={**HEADERS, "Content-Type": "application/json"}, data=json.dumps({"prefixes": [key]}), timeout=60)
check("test file removed again", rm.status_code == 200, rm.status_code)

print()
if failures:
    print("%d check(s) FAILED: %s" % (len(failures), "; ".join(failures)))
    sys.exit(1)
print("all checks passed")
