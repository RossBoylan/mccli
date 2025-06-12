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
import json
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

DATADIR = Path.cwd()  # assume we are running from top of the analysis directory.

MYNODE = shutil.which("node")
MYPY = sys.executable  # the one in the virtual environment
MYMC = str(Path(__file__).parent.parent / "mc.js")

with open(Path('MC/inputs/input_data.json')) as f:
    input_data = json.load(f)

def file_filter(theDir, theList):
    """Return elements of theList to exclude from copying.
    This is for use by shutil.copytree."""
    exclude = []
    myprog = (input_data['model']+".exe").lower()
    if Path(theDir) == DATADIR:
        # yes, "output"
        keep_dirs = ("input", "modfile", "output")
        for x in theList:
            p = DATADIR / x
            if p.is_dir():
                if x in keep_dirs:
                    continue
                else:
                    exclude.append(x)
            elif p.suffix.lower() in (".inp", ".out", ".frmt", ".dat", ".txt") or \
                p.name.lower() in ("outfile.dat", myprog):
                continue         
            else:
                exclude.append(x)
    return exclude

def prepare_one(inp_file, input_data, pdir, inp_distribution):
    """prepare a single directory for a parallel run
    inp_file: the input file to use (no extension) <str>
    input_data: JSON object with original input data
    pdir: directory under which individual parallel directories go <Path>
    inp_distribution: path from which to copy the distributions <Path>

    Creates a directory under pdir named inp_file and copies stuff from
    the master, modifying as necessary.

    Many of these things seem like good candidates for symlinks,
    but the system has a nasty habit of writing over input files and directories.
    So, for safety, we copy everything.

    The one exception is that the MC directory will be a symlink back to
    an appropriately named directory MC_{inp_file} under the main project.
    """
    realMC = DATADIR / f"MC_{inp_file}"
    realMC.mkdir(exist_ok=True)
    pproj = pdir / inp_file  # will be created by copytree
    shutil.copytree(DATADIR, pproj, ignore=file_filter)
    (pproj / "MC").symlink_to(realMC, target_is_directory=True)
    (pproj / "MC" / "inputs").mkdir()
    custom = input_data.copy()
    custom["inp_files"] = [inp_file]
    with open(pproj / "MC" / "inputs" / "input_data.json", 'w') as f:
        json.dump(custom, f, indent=4)
    # probably the next could be a symlink, but it is safer to copy
    shutil.copy2(inp_distribution, pproj / "MC" / "inputs" / "inp_distribution.txt")


def prepare():
    """Prepare directories for simulation"""

    inp_files = input_data['inp_files']
    pdir = Path("./parallel")
    if not pdir.exists():
        pdir.mkdir()
    inp_distribution = Path('MC/inputs/inp_distribution.txt')
    if not inp_distribution.exists():
        inp_distribution = Path("./inp_distribution.txt")
        if not inp_distribution.exists():
            raise FileNotFoundError("inp_distribution.txt not found in MC/inputs or top directory.")
    for inp_file in inp_files:
        prepare_one(inp_file, input_data, pdir, inp_distribution)


prepare()

def do_run():
    "stub of code to do a single simulation run"
    # --overwrite is a dangerous option.
    cmd = [MYNODE, MYMC]+("run 2 0 345 --json --overwrite --python".split())+[MYPY]
    r = subprocess.Popen(cmd, 
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True)
    for line in r.stdout: # type: ignore
        if not line:
            break
        try:
            data = json.loads(line)
        except json.decoder.JSONDecodeError:
            data = line.rstrip()
            print("Encountered non-JSON output from mc runSims, treating as text.")
        print(data)

    print(f"Done with status {r.returncode}.")
    r.wait(10)  # wait for it to finish, if it hasn't already
