# SPDX-FileCopyrightText: 2026 edgecoil
# SPDX-License-Identifier: MIT
"""CI: rebuild a board that vendors this toolkit, with THIS toolkit, and require every board to come
out canonically identical to its committed design.

    python3 ci/downstream.py <board repo checkout> <name>

A toolkit change that alters any board's output fails here, before that board picks it up. If the
change is meant to alter output, gate it behind a Config flag (default off), as the pipeline does.
The board's own vendored copy is replaced in the checkout, which CI throws away afterwards.
"""
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Each board: where its build lives in its repo, its vendor dir, and its boards' file paths.
BOARDS = {
    "cec-bridge": dict(build="cec-bridge", vendor="vendor",
                       boards={"cec-bridge": "cec-bridge/cec-bridge/cec-bridge"}),
    "tune-button": dict(build="hardware/pcb", vendor="hardware/pcb/vendor",
                        boards={v: f"hardware/pcb/{v}/tune-button-{v}" for v in ("xiao", "c3", "c3-jst")}),
}

repo, name = os.path.abspath(sys.argv[1]), sys.argv[2]
cfg = BOARDS[name]
saved = tempfile.mkdtemp(prefix="committed-")
for v, base in cfg["boards"].items():
    os.makedirs(os.path.join(saved, v))
    for ext in ("kicad_pcb", "kicad_pro", "kicad_dru"):
        src = os.path.join(repo, f"{base}.{ext}")
        if os.path.exists(src):
            shutil.copy(src, os.path.join(saved, v))

vend = os.path.join(repo, cfg["vendor"], "edgecoil_pcb")
if not os.path.isdir(vend):
    sys.exit(f"downstream: {name} has no vendored edgecoil_pcb at {cfg['vendor']}")
shutil.rmtree(vend)
shutil.copytree(os.path.join(ROOT, "edgecoil_pcb"), vend, ignore=shutil.ignore_patterns("__pycache__"))

r = subprocess.run(["./build.sh", *cfg["boards"]], cwd=os.path.join(repo, cfg["build"]))
if r.returncode:
    sys.exit(f"downstream: {name} build failed with this toolkit")

bad = []
for v, base in cfg["boards"].items():
    committed = os.path.join(saved, v, os.path.basename(base) + ".kicad_pcb")
    c = subprocess.run([sys.executable, "-m", "edgecoil_pcb.canon", committed, os.path.join(repo, base + ".kicad_pcb")],
                       env=dict(os.environ, PYTHONPATH=ROOT), capture_output=True, text=True)
    out = "\n".join(l for l in (c.stdout + c.stderr).splitlines() if "Debug:" not in l)
    print(f"downstream: {name}/{v}: {out.splitlines()[-1] if out else ''}")
    if c.returncode:
        bad.append(v)
        print(out[-3000:])
if bad:
    sys.exit(f"downstream: {name}: {', '.join(bad)} changed with this toolkit")
