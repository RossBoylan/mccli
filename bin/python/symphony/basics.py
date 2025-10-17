import json
from pathlib import Path
import shutil
import sys

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
        self.MYROOT = Path(__file__).parent.parent.parent.parent
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
        self.MYMC = str(self.MYROOT / "bin" / "mc.js")

        with open(Path('MC/inputs/input_data.json')) as f:
            self.input_data = json.load(f)

        # the following are filled in later
        # defined here for reference and to quiet type check warnings
        self.pdir = Path()
        self.inp_files = []
        self.inp_distribution = Path()