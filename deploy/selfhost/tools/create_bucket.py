"""Create the private bucket for uploaded documents (idempotent). Runs inside the app container."""
import json
import os
import sys

import requests

base = os.environ["EXCHANGE_SUPABASE_URL"].rstrip("/")
key = os.environ["EXCHANGE_SUPABASE_SECRET_KEY"]
name = "exchange-private-vault"
headers = {"Authorization": "Bearer " + key, "apikey": key, "Content-Type": "application/json"}

current = requests.get(base + "/storage/v1/bucket/" + name, headers=headers, timeout=30)
if current.status_code == 200:
    if current.json().get("public") is not False:
        sys.exit("bucket exists but is not private - fix it before going on")
    print("bucket already exists and is private")
    sys.exit(0)
created = requests.post(base + "/storage/v1/bucket", headers=headers,
                        data=json.dumps({"id": name, "name": name, "public": False}), timeout=30)
if created.status_code != 200:
    sys.exit("could not create the bucket: HTTP %s %s" % (created.status_code, created.text[:300]))
check = requests.get(base + "/storage/v1/bucket/" + name, headers=headers, timeout=30).json()
if check.get("public") is not False:
    sys.exit("bucket was created but is not private")
print("bucket created and private")
