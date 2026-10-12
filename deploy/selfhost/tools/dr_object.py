"""Disaster-recovery rehearsal helper: put a known object in the private bucket, or check that it is still there.

  python /opt/selfhost/dr_object.py put     stores a fixed 4 KiB object and prints its SHA-256
  python /opt/selfhost/dr_object.py check   downloads it again and compares
"""
import hashlib
import os
import sys

import requests

BASE = os.environ["EXCHANGE_SUPABASE_URL"].rstrip("/")
KEY = os.environ["EXCHANGE_SUPABASE_SECRET_KEY"]
HEADERS = {"Authorization": "Bearer " + KEY, "apikey": KEY}
BUCKET, NAME = "exchange-private-vault", "vault/dr-rehearsal/object.bin"
PAYLOAD = hashlib.sha256(b"uniway-dr-rehearsal").digest() * 128      # 4096 bytes, always the same
DIGEST = hashlib.sha256(PAYLOAD).hexdigest()

if len(sys.argv) < 2 or sys.argv[1] not in ("put", "check"):
    sys.exit("usage: dr_object.py put|check")
if sys.argv[1] == "put":
    r = requests.post("%s/storage/v1/object/%s/%s" % (BASE, BUCKET, NAME), headers={**HEADERS, "Content-Type": "application/octet-stream", "x-upsert": "true"}, data=PAYLOAD, timeout=60)
    print("stored" if r.status_code == 200 else "FAILED %s %s" % (r.status_code, r.text[:200]), DIGEST)
    sys.exit(0 if r.status_code == 200 else 1)
r = requests.get("%s/storage/v1/object/authenticated/%s/%s" % (BASE, BUCKET, NAME), headers=HEADERS, timeout=60)
ok = r.status_code == 200 and hashlib.sha256(r.content).hexdigest() == DIGEST
print("object is back and identical" if ok else "object missing or different (HTTP %s)" % r.status_code)
sys.exit(0 if ok else 1)
