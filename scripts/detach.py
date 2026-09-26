#!/usr/bin/env python3
"""Launch a long job detached from the current terminal session (stdout/stderr to a log) and print the PID.

  python3 scripts/detach.py <logfile> <command...>
  python3 scripts/detach.py houses/my_house/output/runs/arrive.log \
      python -m archviz.production --scene houses/my_house/output/arrive.blend \
      --out houses/my_house/output/runs/arrive --shot arrive

Background jobs tied to an interactive or automated shell can be killed when that shell exits; a process started
with start_new_session=True survives it.  Check progress with `tail -f <logfile>`.
"""
import os, subprocess, sys

if len(sys.argv) < 3:
    sys.exit(__doc__)
log, cmd = sys.argv[1], sys.argv[2:]
os.makedirs(os.path.dirname(os.path.abspath(log)) or ".", exist_ok=True)
f = open(log, "ab")
p = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, start_new_session=True, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print(f"[detach] pid {p.pid} -> {log}")
