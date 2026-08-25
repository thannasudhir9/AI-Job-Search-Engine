import glob
import sys
from pypdf import PdfReader

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

paths = [
    r"C:\Users\thann\Downloads\Sudhir_CV_21Feb2026_DE.docx(2) (1).pdf",
    r"C:\Users\thann\Downloads\Sudhir_CV_21Feb2026_DE.docx(2).pdf",
]
target = None
for p in paths:
    try:
        if __import__("os").path.exists(p):
            target = p
            break
    except OSError:
        pass
if not target:
    hits = glob.glob(r"C:\Users\thann\Downloads\Sudhir_CV*")
    target = hits[0] if hits else None
if not target:
    print("NOT_FOUND")
    sys.exit(1)

reader = PdfReader(target)
text = "\n".join((page.extract_text() or "") for page in reader.pages)
print(f"FILE: {target}")
print(f"PAGES: {len(reader.pages)}")
print("=" * 60)
print(text.strip())
