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
from datetime import datetime
import json
from pathlib import Path
import shutil
import sys

mysymphony = str((Path(__file__).parent) / "symphony")
if mysymphony not in sys.path:
    sys.path.append(mysymphony)
from prepare import prepare, prepareOne
from switchboard import SwitchBoard
from message_handlers import *
from run import *

class Basics:
    """Holds shared variables and ensures basic setup
    Makes a number of specific choices you may want to
    change.

    This is little more than a space to put shared variables
    into, with the risks posed by global variables.

    Other code, in particular prepare(), writes additional
    information into this object.
    """
    def __init__(self):
        self.MYROOT = Path(__file__).parent.parent.parent
        # This is the root of the mccli software

        ## First time cheat setup for the software
        ## Also sets variables with key locations

        self.OTHERME = self.MYROOT.parent / "mccli-repeatable"
        self.NODE_MODULES = self.MYROOT / "node_modules"
        if not self.NODE_MODULES.exists():
            self.NODE_MODULES.symlink_to(self.OTHERME / "node_modules",
                                    target_is_directory=True)
        self.PYENV = self.MYROOT / "pyenv"
        if not self.PYENV.exists():
            self.PYENV.symlink_to(self.OTHERME / "pyenv", target_is_directory=True)

        self.DATADIR = Path.cwd()  # assume we are running from top of the analysis directory.

        self.MYNODE = shutil.which("node")
        self.MYPY = sys.executable  # the one in the virtual environment
        self.MYMC = str(Path(__file__).parent.parent / "mc.js")

        with open(Path('MC/inputs/input_data.json')) as f:
            self.input_data = json.load(f)

basics = Basics()

async def main(basics: Basics):
    """top-level driver.
    Ordinarily prepares and runs the simulations.
    """
    prepare(basics)
    switch = SwitchBoard()
    switch.addSyncFunction(DumbTerminalLog())
    switch.addSyncFunction(StupidLogfile(basics.pdir / "runlog.txt"))
    runs = [SingleScenarioRun(basics, scenario, iterations=1001, seed=345).run(switch)
             for scenario in basics.inp_files ]
    x = switch.message_obj({"type": "INFO", "text": "Maestro begins {len(runs)} parallel runs at {datetime.now()}\n"})
    rvals = await asyncio.gather(*runs)
    x = await switch.message_obj({"type": "INFO", "text": "Maestro finishes {len(runs)} parallel runs at {datetime.now()}\n"})
    switch.close()

asyncio.run(main(basics))