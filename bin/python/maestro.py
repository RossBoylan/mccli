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
import asyncio
import json
from pathlib import Path
import shutil
import subprocess
import sys

MYROOT = Path(__file__).parent.parent.parent
# This is the root of the mccli software

## First time cheat setup for the software
## Also sets variables with key locations

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
    global input_data
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

class AbstractRun:
    """Describes and manages a single `mc run` invocation.
    A run may cover one more scenarios (`.inp` files) and may 
    cover all or some of the iterations of interest.
    A run takes place in a single directory, which takes
    the role of root of the data directories for a project.

    Subclasses must implement the following methods
    root()->Path the top level directory from which the simulations run
    name()->str  a human-friendly name for the run, usual same as last 
                  component of root
    lasti()->int  last iteration number completed
    startTime()->DateTime or None.  When this whole run began.
    lastiTime()->DateTime or None. When iteration lasti finished.
    averageTime()->timedelta Average time for one iteration.
    longestTime()->timedelta longest time for one iteration
    shortestTime()->timedelta shortest time for one iteration
    The timing information should exclude iteration 0 if possible,
    since it involves less processing.
    remainingIterations()  number iterations left
    completeIterations() number of iterations completed
    averageTimeRemaining() timedelta until completion
    optimisticTimeRemaining()
    pessimisticTimeRemaining()
    completionTime() DateTime estimated based on averageTime
    optimisticCompletionTime() DateTime
    pessimisticCompletionTime() DateTime

    The system hits patches of extreme slowness, and so the length
    of time an iteration takes is expected to vary.  The remaining
    iterations may occur during an unusually slow or fast period;
    the optimistic estimates assume remining iterations will be fast,
    and the pessimistic ones assume it will be slow.

    """
    _instances = {}  # keys are ids, values are instances of AbstractRun subclasses

    @staticmethod
    def _newrun(aRun: "AbstractRun")->int:
        "register a new run object, returning and setting its id"
        i = len(AbstractRun._instances)+1
        aRun._id = i
        AbstractRun._instances[i] = aRun
        return i
    
    def __init__(self):
        self._newrun(self)

class SingleScenarioRun(AbstractRun):
    """Does a complete run of a single .inp scenario.

    Currently runs with --overwrite, a dangerous option.
    This is to permit repeated testing.
    """
    def __init__(self, parallelDir: Path, scenario: str, iterations=1001, seed=345):
        super().__init__()
        self._root = parallelDir / scenario
        self._scenario = scenario
        self._cmd = [MYNODE, MYMC, "run", str(iterations), "0", str(seed),
                     "--json", "--overwrite", "--python", MYPY]
        self._niter = iterations
        self._lasti = -1
        self._startTime = None
        self._status = "starting"

    def root(self):
        "top directory for data files. Will be working directory for programs."
        return self._root
    
    def name(self)->str:
        "friendly name for self"
        return self._scenario
    
    def lasti(self)->int:
        """last iteration completed.
        This is the index number of the iteration; if a run is iterations
        500-600 and 501 is the last one completed, this function returns 501,
        not 1 or 2.
        <0 means nothing done
        """
        return self._lasti
    
    def remainingIterations(self)->int:
        "Number of iterations still to go"
        # this logic would not work for partial runs
        return self._niter - self._lasti-1
    
    def completeIterations(self)->int:
        "Iterations done, remembering we start at 0"
        return 1+self._lasti
    
    async def run(self, switchboard)->int:
        """Run the job, reporting results to switchboard in real time.
        """
        self._status = "running"
        p = await asyncio.create_subprocess_exec(*cmd, 
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        taskout = None
        taskerr = None
        while not (p.stdout.at_eof() and p.stderr.at_eof()):
            if taskout is None:
                taskout = asyncio.create_task(p.stdout.readline(), name="stdout")
            if taskerr is None:
                taskerr = asyncio.create_task(p.stderr.readline(), name="stderr")
            done, pending = await asyncio.wait(
                [taskout, taskerr],
                return_when=asyncio.FIRST_COMPLETED)
            for s in done:
                line = s.result()
                # I generally get back 0 byte string for stderr even when nothing was written to stderr
                n = len(line)
                if n:
                    line = line.decode().rstrip()
                if s.get_name() == "stderr":
                    taskerr = None
                    if n:
                        # everything to stderr is plain text
                        # make fake JSON object
                        m = {"type": "ERR", "text": line,
                             "runid": self._id, "lasti": self._lasti}
                        self._failed(m)
                        switchboard.message_obj(m)

                else:
                    taskout = None
                    if n:
                        try:
                            data = json.loads(line)
                            if data["type"] == "ERR":
                                self._failed(data)
                        except json.decoder.JSONDecodeError:
                            data = line.rstrip()
                            data = {"type": "stdout", "text": data,
                                    "runid": self._id, "lasti": self._lasti}
                        switchboard.message_obj(data)
                            

        if self._status != "error":
            self._status = "done"
        return p.returncode

    def _failed(self, obj):
        """Note failure with associated JSON object
        Should I abort here?"""
        self._status = "error"
        self._status_info = obj

