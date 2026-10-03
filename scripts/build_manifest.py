"""Collect the files placed in files/ and prepare them for the app.

Rules used to recognise a file from its name:
  - .html / .htm            -> mock test
  - .pdf with key/ans/solution in the name (or named like k01.pdf) -> answer key
  - any other .pdf          -> question paper
  - set number = the first 1-2 digit number found in the file name
    (e.g. "VP AIR 4 Question Paper.pdf", "Test-07 key.pdf", "p03.pdf")

Files are copied to www/files/ with clean names (p01.pdf, k01.pdf, m01.html)
and www/files/manifest.json is written for the app.
"""
import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "files")
OUT = os.path.join(ROOT, "www", "files")
PREFIX = {"paper": "p", "key": "k", "mock": "m"}


def classify(name):
    base, ext = os.path.splitext(name)
    ext = ext.lower()
    low = base.lower()
    if ext in (".html", ".htm"):
        kind = "mock"
    elif ext == ".pdf":
        if (
            re.search(r"key|ans|solution", low)
            or re.search(r"(?:^|[^a-z])(?:ak|sol)(?:[^a-z]|$)", low)
            or re.match(r"^k[\s_\-]*\d", low)
        ):
            kind = "key"
        else:
            kind = "paper"
    else:
        return None
    # prefer a number written right after test/part/set/air (e.g. test01, Part Test-04, AIR 4)
    m = re.search(r"(?:test|part|set|air)[\s_\-]*0*(\d{1,2})(?!\d)", low)
    if m:
        n = int(m.group(1))
    else:
        nums = [int(x) for x in re.findall(r"\d+", base) if len(x) <= 2]
        if not nums:
            return None
        n = nums[0]
    return n, kind, ".html" if kind == "mock" else ".pdf"


def copy_mock(src, dst):
    """Copy a mock test and add the result-saving hook just before </body>."""
    with open(os.path.join(ROOT, "scripts", "record_hook.js"), encoding="utf-8") as f:
        hook = f.read()
    with open(src, "r", encoding="utf-8", errors="surrogateescape", newline="") as f:
        html = f.read()
    if 'id="vpair-hook"' not in html:
        tag = '<script id="vpair-hook">\n' + hook + "\n</script>\n"
        i = html.lower().rfind("</body>")
        html = html[:i] + tag + html[i:] if i != -1 else html + "\n" + tag
    with open(dst, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
        f.write(html)


def main():
    if not os.path.isdir(SRC):
        print("ERROR: 'files/' folder not found. Put your PDFs and HTML files in it.")
        sys.exit(1)

    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT)

    found = {}
    skipped = []
    conflicts = []

    for name in sorted(os.listdir(SRC)):
        path = os.path.join(SRC, name)
        if not os.path.isfile(path):
            continue
        res = classify(name)
        if not res:
            skipped.append(name)
            continue
        n, kind, ext = res
        if (n, kind) in found:
            conflicts.append("Set %d %s: '%s' and '%s'" % (n, kind, found[(n, kind)], name))
            continue
        found[(n, kind)] = name
        dest = os.path.join(OUT, "%s%02d%s" % (PREFIX[kind], n, ext))
        if kind == "mock":
            copy_mock(path, dest)
        else:
            shutil.copyfile(path, dest)

    manifest = {}
    for (n, kind), name in sorted(found.items()):
        ext = ".html" if kind == "mock" else ".pdf"
        manifest.setdefault(str(n), {})[kind] = "files/%s%02d%s" % (PREFIX[kind], n, ext)
        print("set %02d  %-6s <- %s" % (n, kind, name))

    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    for s in sorted(manifest, key=int):
        missing = [k for k in ("paper", "key", "mock") if k not in manifest[s]]
        if missing:
            print("WARNING: set %s has no %s" % (s, ", ".join(missing)))
    for name in skipped:
        print("skipped (not recognised): " + name)

    if conflicts:
        print("\nERROR: two files match the same slot, rename one of them:")
        for c in conflicts:
            print("  - " + c)
        sys.exit(1)
    if not manifest:
        print("ERROR: no usable files found in files/")
        sys.exit(1)
    print("\n%d sets ready." % len(manifest))


if __name__ == "__main__":
    main()
      
