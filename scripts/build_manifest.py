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


# Every mock test was built from a slightly different template, so each one gets a small
# patch at the start of its own submit function. The patch hands the questions, the user's
# answers and the time left to window.__vpCapture (see record_hook.js).
TEMPLATES = [
    {
        "name": "Test 01/02 style (QUESTIONS + responses)",
        "must": [r"const QUESTIONS = window\.__QDATA__", r"const responses = \{\}"],
        "anchor": r"function submitTest\s*\(\s*\)\s*\{",
        "js": "__vpCapture(QUESTIONS, function(i){return responses[QUESTIONS[i].id];}, timeLeft, TOTAL_TIME_SECONDS);",
    },
    {
        "name": "Test 03 style (DATA + answers[])",
        "must": [r"const DATA = JSON\.parse\(document\.getElementById\('dataScript'\)"],
        "anchor": r"function submitTest\s*\(\s*\)\s*\{",
        "js": "__vpCapture(DATA.map(function(d){return {id:d.n,subject:d.subject,answer:d.correct};}), function(i){return answers[i+1];}, timeLeft, 180*60);",
    },
    {
        "name": "Test 04 style (selected{})",
        "must": [r"const selected = \{\};\s*// qid"],
        "anchor": r"function submitTest\s*\(\s*\)\s*\{",
        "js": "__vpCapture(QDATA, function(i){return selected[QDATA[i].id];}, timeLeft, TOTAL_SECONDS);",
    },
    {
        "name": "Test 05 style (responses{} + doSubmit)",
        "must": [r"let responses = \{\};\s*// qid", r"function doSubmit"],
        "anchor": r"function doSubmit\s*\(\s*\)\s*\{",
        "js": "__vpCapture(QDATA, function(i){return responses[QDATA[i].id];}, timeLeft, TOTAL_SECONDS);",
    },
    {
        "name": "Test 06 style (state.answers)",
        "must": [r"answers:\s*\{\},\s*// id", r"function submitTest\s*\(\s*auto\s*\)"],
        "anchor": r"function submitTest\s*\(\s*auto\s*\)\s*\{",
        "js": "__vpCapture(QDATA, function(i){return state.answers[QDATA[i].id];}, state.remaining, DURATION_SEC);",
    },
    {
        "name": "Test 07 style (state[i].selected)",
        "must": [r"const state = QDATA\.map\(\(\)=>\(\{status:'notvisited', selected:null\}\)\)"],
        "anchor": r"function submitTest\s*\(\s*\)\s*\{",
        "js": "__vpCapture(QDATA, function(i){return state[i].selected;}, timeLeft, TOTAL_TIME);",
    },
    {
        "name": "Test 08 style (DATA.answers + userAns[])",
        "must": [r"app-data-holder", r"function showResults"],
        "anchor": r"function showResults\s*\(\s*\)\s*\{",
        "js": "__vpCapture(DATA.answers.map(function(a,i){var r=subjectRanges.filter(function(x){return i>=x.start&&i<x.end;})[0];return {id:i+1,subject:r?r.name:'',answer:a};}), function(i){return userAns[i];}, timeLeft, 180*60);",
    },
    {
        "name": "Test 09 style (state[i].answer)",
        "must": [r"const state = QDATA\.map\(\(\)=>\(\{answer:null"],
        "anchor": r"function doSubmit\s*\(\s*\)\s*\{",
        "js": "__vpCapture(QDATA.map(function(q){return {id:q.id,subject:q.subject,answer:q.answer,alt:q.altAnswer};}), function(i){return state[i].answer;}, timeLeft, TOTAL_TIME);",
    },
    {
        "name": "Test 10 style (state.selected{})",
        "must": [r"selected:\s*\{\},\s*// qid -> option number"],
        "anchor": r"function submitTest\s*\(\s*\)\s*\{",
        "js": "__vpCapture(QDATA, function(i){return state.selected[QDATA[i].id];}, state.timeLeft, DURATION_SEC);",
    },
]


def patch_submit(html):
    """Return (patched_html, template_name or None)."""
    for t in TEMPLATES:
        if all(re.search(p, html) for p in t["must"]):
            m = re.search(t["anchor"], html)
            if not m:
                return html, None
            return html[: m.end()] + "\n" + t["js"] + "\n" + html[m.end():], t["name"]
    return html, None


def copy_mock(src, dst):
    """Copy a mock test, patch its submit function and add the result-saving hook."""
    with open(os.path.join(ROOT, "scripts", "record_hook.js"), encoding="utf-8") as f:
        hook = f.read()
    with open(src, "r", encoding="utf-8", errors="surrogateescape", newline="") as f:
        html = f.read()
    name = None
    if 'id="vpair-hook"' not in html:
        html, name = patch_submit(html)
        tag = '<script id="vpair-hook">\n' + hook + "\n</script>\n"
        i = html.lower().rfind("</body>")
        html = html[:i] + tag + html[i:] if i != -1 else html + "\n" + tag
    with open(dst, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
        f.write(html)
    return name


def main():
    if not os.path.isdir(SRC):
        print("ERROR: 'files/' folder not found. Put your PDFs and HTML files in it.")
        sys.exit(1)

    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT)

    found = {}
    patched = {}
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
            tname = copy_mock(path, dest)
            patched[(n, kind)] = tname
        else:
            shutil.copyfile(path, dest)

    manifest = {}
    for (n, kind), name in sorted(found.items()):
        ext = ".html" if kind == "mock" else ".pdf"
        manifest.setdefault(str(n), {})[kind] = "files/%s%02d%s" % (PREFIX[kind], n, ext)
        print("set %02d  %-6s <- %s" % (n, kind, name))

    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    for (n, kind), tname in sorted(patched.items()):
        if tname:
            print("record hook ok  set %02d  (%s)" % (n, tname))
        else:
            print("WARNING: set %02d mock test is a new layout, its result will NOT be saved in Test Records" % n)

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

