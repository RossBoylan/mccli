# orchestrate parallel runs of the monte carlo simulator

# File: maestro.py
# Author: Ross Boylan
# Created: 2025-06-06

# There are two major parts, preparation and execution.
#
# Prequisite: mc init has been run and *all* the .inp files targeted 
# for parallelization have been given to it.  For now, also assume 
# that the post-initialization manual steps, which is mostly copying 
# inp_distributions.txt to the right place, have also been done.
# It is best to do this from a relatively clean directory to avoid 
# unnecessary copying.

# Preparation: Duplicate the project directory multiple times,
# using copy or link as appropriate.  This also requires setting on
# short names for each input file, to be used in various places, most
# notably MC_xxx directories under the main project that will show 
# the result. 
# 
# Finally, since the original was designed to run all .inp files at 
# once, each duplicate must be customized to run only one .inp file.
#  
#
# Execution: Execute appropriate `node mc runSims` for each copy,
# in parallel.  This code is written assuming it has terminal for
# which runSims can control positions on the stream.  So they need
# an appropriate environment, and this program must have a reasonable
# way to display overall status and, if necessary, details for 
# individual simulations.
#
# Once execution finishes various cleanup or file copying operations 
# may be necessary.
from pathlib import Path
import shutil
import subprocess
import sys

MYROOT = Path(__file__).parent.parent.parent
# This is the root of the project, not the root of the virtual environment.

OTHERME = MYROOT.parent / "mccli-repeatable"
NODE_MODULES = MYROOT / "node_modules"
if not NODE_MODULES.exists():
    NODE_MODULES.symlink_to(OTHERME / "node_modules",
                             target_is_directory=True)
PYENV = MYROOT / "pyenv"
if not PYENV.exists():
    PYENV.symlink_to(OTHERME / "pyenv", target_is_directory=True)

sys.exit(0         )

MYNODE = shutil.which("node")
MYPY = sys.executable  # the one in the virtual environment
MYMC = str(Path(__file__).parent.parent / "mc.js")
cmd = [MYNODE, MYMC]+("run 2 0 345 --python".split())+[MYPY]
r = subprocess.Popen(cmd, 
                     stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT,
                     text=True)
for line in r.stdout:
    if not line:
        break
    print(line, end="")

print(f"Done with status {r.returncode}.")
