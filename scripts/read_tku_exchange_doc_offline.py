"""Extract a captured exchange DOC offline with macros/link updates disabled.

Keep the original capture unchanged; retain a separately identified text review.
No document interaction, form submission, or requested network operation occurs.
"""
import argparse
import gzip
import hashlib
import json
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from tku_capture_io import BUNDLE, exists, read_bytes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source_id")
    ap.add_argument("institution_id")
    ap.add_argument("--render-pdf", action="store_true", help="Retain PDF rendering and page text for layout review")
    args = ap.parse_args()
    old = json.loads(gzip.decompress(read_bytes(BUNDLE / "host_census_sources" / (args.source_id + ".json.gz"))))
    assert old["http_status"] == 200 and old["local_file"].endswith(".doc")
    binary = read_bytes(BUNDLE / "host_census_sources" / old["local_file"])
    assert hashlib.sha256(binary).hexdigest() == old["sha256"]
    mode = "pdf" if args.render_pdf else "text"
    derived_id = hashlib.sha256((args.source_id + ":offline-libreoffice-exchange-" + mode + "-20261011").encode()).hexdigest()[:24]
    destination = BUNDLE / "host_census_sources" / (derived_id + ".json.gz")
    if exists(destination):
        print(json.dumps(dict(status="retained_immutable_offline_review", source_id=derived_id)))
        return
    soffice = shutil.which("soffice")
    if not soffice:
        raise RuntimeError("Installed LibreOffice soffice command unavailable; DOC body not reviewed")
    with tempfile.TemporaryDirectory(prefix="tku-exchange-doc-") as directory:
        base = Path(directory)
        profile = base / "profile"
        (profile / "user").mkdir(parents=True)
        (profile / "user/registrymodifications.xcu").write_text('''<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry">
<item oor:path="/org.openoffice.Office.Common/Security/Scripting"><prop oor:name="MacroSecurityLevel" oor:op="fuse"><value>3</value></prop></item>
<item oor:path="/org.openoffice.Office.Writer/Content/Update"><prop oor:name="Link" oor:op="fuse"><value>0</value></prop></item>
</oor:items>''')
        input_path = base / (args.source_id + ".doc")
        input_path.write_bytes(binary)
        export_filter = "pdf:writer_pdf_Export" if args.render_pdf else "txt:Text"
        result = subprocess.run([soffice, "-env:UserInstallation=" + profile.as_uri(), "--headless", "--convert-to", export_filter, "--outdir", directory, str(input_path)], capture_output=True, text=True, timeout=45)
        output = input_path.with_suffix(".pdf" if args.render_pdf else ".txt")
        if result.returncode or not output.is_file():
            raise RuntimeError(f"Offline DOC conversion failed ({result.returncode}): {result.stderr[:1000]}")
        raw = output.read_bytes()
        if args.render_pdf:
            from pypdf import PdfReader
            pages = [dict(page=i, text=page.extract_text() or "") for i, page in enumerate(PdfReader(output).pages, 1)]
            text = "\n".join(page["text"] for page in pages)
        else:
            pages = []
            text = raw.decode("utf-8-sig")
        assert len(text.strip()) >= 50, "DOC conversion yielded no usable body"
        version = subprocess.run([soffice, "--version"], capture_output=True, text=True, timeout=10).stdout.strip()
        text_bytes = text.encode("utf-8")
        parser = dict(tool=version, mode="headless " + export_filter + " conversion", macro_security_level=3, external_link_update=0, requested_network_operations=0, conversion_exit_code=result.returncode, conversion_warning=result.stderr[:2000], converted_text_sha256=hashlib.sha256(text_bytes).hexdigest(), converted_text_bytes=len(text_bytes))
    stamp = datetime.now(timezone.utc).isoformat()
    derived = dict(old, id=derived_id, text=text, paragraphs=[line.strip() for line in text.splitlines() if line.strip()], checked_at=stamp, original_capture_id=args.source_id, content_extraction_status="parsed_legacy_DOC_text_offline", parser=parser)
    if args.render_pdf:
        rendered_file = derived_id + "-offline-render.pdf"
        (BUNDLE / "host_census_sources" / rendered_file).write_bytes(raw)
        derived.update(pages=pages, rendered_file=rendered_file, rendered_sha256=hashlib.sha256(raw).hexdigest(), rendered_bytes=len(raw))
    destination.write_bytes(gzip.compress(json.dumps(derived, ensure_ascii=False).encode(), mtime=0))
    path = BUNDLE / "host_census_capture_index.json"
    index = json.loads(path.read_text())
    row = next(r for r in index if r["id"] == args.institution_id)
    meta = {key: derived.get(key) for key in ("id", "source_url", "final_url", "http_status", "checked_at", "sha256", "title", "error")}
    meta.update(source_role="offline_macro_disabled_DOC_content_review", original_capture_id=args.source_id, scope="Body extracted; applicable year and programme require separate content review")
    row["sources"].append(meta)
    path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(dict(source_id=derived_id, original_capture_id=args.source_id, parser=parser), ensure_ascii=False))


if __name__ == "__main__":
    main()
