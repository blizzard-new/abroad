import glob
import os
from pypdf import PdfReader

pdf_dir = "/app/sources/kmu"
out_lines = []
for path in sorted(glob.glob(os.path.join(pdf_dir, "*.pdf"))):
    fname = os.path.basename(path)
    out_lines.append(f"=== PDF: {fname} ({os.path.getsize(path)} bytes) ===")
    try:
        reader = PdfReader(path)
        out_lines.append(f"Pages: {len(reader.pages)}")
        for idx, page in enumerate(reader.pages):
            txt = page.extract_text() or ""
            out_lines.append(f"--- Page {idx+1} ---")
            out_lines.append(txt.strip())
    except Exception as e:
        out_lines.append(f"ERROR: {e}")

with open("/app/sources/kmu/parsed_pdfs_utf8.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines))
print("Parsed PDFs successfully.")
