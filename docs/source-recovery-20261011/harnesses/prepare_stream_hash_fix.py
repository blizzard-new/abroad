from pathlib import Path
import os,sys
r=Path(sys.argv[1])/'src/exchange_info'
def replace(n,s):
 p=r/n;t=p.with_name(p.name+'.memory-fix');t.write_text(s);os.replace(t,p)
replace('source_integrity.py','''"""Hash source files without retaining full PDFs or response archives in memory."""
import gzip
import hashlib


def file_sha256(path, *, compressed=False):
    opener = gzip.open if compressed else open
    with opener(path, "rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()
''')
s=(r/'ccu_overseas.py').read_text().replace('from .models import (','from .source_integrity import file_sha256\nfrom .models import (')
s=s.replace('            contents = (BUNDLE / source["bundled_file"]).read_bytes()\n            if hashlib.sha256(contents).hexdigest() != source["sha256"]:', '            if file_sha256(BUNDLE / source["bundled_file"]) != source["sha256"]:')
replace('ccu_overseas.py',s)
s=(r/'ccu_profile.py').read_text().replace('from .models import (','from .source_integrity import file_sha256\nfrom .models import (')
s=s.replace('hashlib.sha256(\n                        (BUNDLE / source["bundled_file"]).read_bytes()\n                    ).hexdigest()', 'file_sha256(BUNDLE / source["bundled_file"])')
replace('ccu_profile.py',s)
s=(r/'ccu_completion_sources.py').read_text().replace('import gzip\n','').replace('import hashlib\n','').replace('from urllib.parse import urlsplit','from urllib.parse import urlsplit\nfrom .source_integrity import file_sha256')
s=s.replace('    raw = raw_path.read_bytes()\n','').replace('hashlib.sha256(raw).hexdigest() != record["stored_sha256"]','file_sha256(raw_path) != record["stored_sha256"]')
s=s.replace('        raw = gzip.decompress(raw)\n','')
s=s.replace('hashlib.sha256(raw).hexdigest() != expected', 'file_sha256(raw_path, compressed=raw_path.suffix == ".gz") != expected')
replace('ccu_completion_sources.py',s)
print('Source PDF and gzip hashes now stream, retaining identical hash checks.')
