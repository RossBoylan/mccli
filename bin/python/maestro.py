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
from datetime import datetime, timedelta
import json
from pathlib import Path
import shutil
import sys

# Get my submodules in the symphony directory
mysymphony = str((Path(__file__).parent) / "symphony")
if mysymphony not in sys.path:
    sys.path.append(mysymphony)
# DEBUG: prepare_basics is for testing, maybe prepare_one too
from prepare import prepare, prepare_one, prepare_basics
from switchboard import SwitchBoard
from message_handlers import *
from run import *
from basics import Basics


basics = Basics()

async def main(basics: Basics):
    """top-level driver.
    Ordinarily prepares and runs the simulations.
    """
    # DEBUG.  Next line usually prepare()
    prepare_basics(basics)
    switch = SwitchBoard()
    niter = 2
    nrun = len(basics.inp_files) # type: ignore
    timer_log = TerminalTimerLog(niter, nrun, updateInterval=timedelta(seconds=45))
    switch.addSyncFunction(timer_log)
    switch.addSyncFunction(StupidLogfile(basics.pdir / "runlog.txt")) # type: ignore
    runs = [SingleScenarioRun(basics, scenario, iterations=niter, seed=345).run(switch)
             for scenario in basics.inp_files ] # type: ignore
    await switch.message_obj({"type": "INFO", "text": f"Maestro begins {len(runs)} parallel runs at {datetime.now()}\n"})
    rvals = await asyncio.gather(*runs)
    await switch.message_obj({"type": "INFO", "text": f"Maestro finishes {len(runs)} parallel runs at {datetime.now()}\n"})
    switch.close()

#asyncio.run(main(basics))
prepare(basics, stemcell="../Justice_Lite3")