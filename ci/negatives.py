# SPDX-FileCopyrightText: 2026 edgecoil
# SPDX-License-Identifier: MIT
"""Negative controls for CI: plant a fault in a copy of a block and require each block test to fail.

    python3 ci/negatives.py

A test that has never failed hasn't been tested. Each case writes a mutated copy to a temporary
directory, runs the test on it, and exits 1 if the test passes the fault. The committed blocks are
never touched.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOCKS = os.path.join(ROOT, "blocks")
env = dict(os.environ, PYTHONPATH=ROOT + os.pathsep + os.environ.get("PYTHONPATH", ""))


def run(cmd):
    return subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)


def mutated_block(tmp, name, change):
    d = os.path.join(tmp, name)
    shutil.copytree(os.path.join(BLOCKS, name), d)
    p = os.path.join(d, "block.json")
    b = json.load(open(p))
    change(b)
    json.dump(b, open(p, "w"), indent=1)
    return d


def move_track(b):  # the first track 20 mm to the side, clear of every pad
    t = b["copper"][0]
    for k in ("start", "end"):
        t[k] = [t[k][0] + 20_000_000, t[k][1]]


def stack_parts(b):  # the second part placed on top of the first: courtyards overlap
    b["parts"][1]["at"] = list(b["parts"][0]["at"])


failures = []
with tempfile.TemporaryDirectory() as tmp:
    cases = [
        ("selftest: a track moved 20 mm",
         ["python3", "-m", "edgecoil_pcb.blocks", "selftest", mutated_block(tmp, "ldo-ldl1117", move_track)]),
    ]
    d = mutated_block(os.path.join(tmp, "drc"), "ldo-ldl1117", stack_parts)
    cases.append(("drc_block: two parts stacked",
                  ["python3", "blocks/tests/drc_block.py", os.path.join(BLOCKS, "ldo-ldl1117"),
                   os.path.join(d, "block.json")]))
    # check_models reads the blocks next to it, so it runs from a copy of the whole blocks tree.
    copy = os.path.join(tmp, "models", "blocks")
    shutil.copytree(BLOCKS, copy)
    inc = os.path.join(copy, "esp32-c3-wroom-02", "model.inc")
    text = open(inc).read()
    assert "R6 3v3 en 10000" in text, "negatives: the R6 line moved; update this control"
    open(inc, "w").write(text.replace("R6 3v3 en 10000", "R6 3v3 en 11000"))
    cases.append(("check_models: R6 10k -> 11k", ["python3", os.path.join(copy, "tests", "check_models.py")]))

    # Each fault must be caught for its own reason, not by a crash: the expected words in the output.
    expect = {cases[0][0]: "reaches no pad", cases[1][0]: "courtyard", cases[2][0]: " BAD "}
    for label, cmd in cases:
        r = run(cmd)
        why = r.stdout + r.stderr
        if r.returncode != 0 and expect[label].lower() not in why.lower():
            failures.append(label)
            print(f"negatives: failed for the wrong reason: {label}\n{why[-800:]}")
            continue
        if r.returncode == 0:
            failures.append(label)
            print(f"negatives: PASSED A PLANTED FAULT: {label}\n{r.stdout[-800:]}")
        else:
            print(f"negatives: caught  {label}")

sys.exit(1 if failures else 0)
