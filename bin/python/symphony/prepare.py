import json
from pathlib import Path
import shutil
import subprocess
import sys

class AFilter:
    """This is the file filter function with a little extra information.
    """
    def __init__(self, basics: "Basics"):
        self.basics = basics
        # and then the stuff we will need
        self.input_data = basics.input_data
        self.DATADIR = basics.DATADIR

    def __call__(self, theDir, theList):
        """Return elements of theList to exclude from copying.
        This is for use by shutil.copytree."""
        exclude = []
        myprog = (self.input_data['model']+".exe").lower()
        if Path(theDir) == self.DATADIR:
            # yes, "output"
            keep_dirs = ("input", "modfile", "output")
            for x in theList:
                p = self.DATADIR / x
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

def prepare_one(inp_file, basics: "Basics"):
    """prepare a single directory for a parallel run
    inp_file: the input file to use (no extension) <str>
    basics: basic info about the project <Basics>.  Will use
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
    if inp_file:
        realMC = basics.DATADIR / f"MC_{inp_file}"
        realMC.mkdir(exist_ok=True)
    pproj = basics.pdir / inp_file  # will be created by copytree
    shutil.copytree(basics.DATADIR, pproj, ignore=AFilter(basics))
    if inp_file:
        (pproj / "MC").symlink_to(realMC, target_is_directory=True)
    (pproj / "MC" / "inputs").mkdir(parents=True)
    custom = basics.input_data.copy()
    if inp_file:
        custom["inp_files"] = [inp_file]
    with open(pproj / "MC" / "inputs" / "input_data.json", 'w') as f:
        json.dump(custom, f, indent=4)
    # probably the next could be a symlink, but it is safer to copy
    shutil.copy2(basics.inp_distribution, pproj / "MC" / "inputs" / "inp_distribution.txt")


def prepare(basics: "Basics", stemcell=None):
    """Prepare directories for simulation
    If stemcell is a string or Path this will make a single copy
    of the directory to that location.
    """

    basics.inp_files = basics.input_data['inp_files']
    basics.pdir = Path("./parallel")
    if not basics.pdir.exists():
        basics.pdir.mkdir()
    inp_distribution = Path('MC/inputs/inp_distribution.txt')
    if not inp_distribution.exists():
        inp_distribution = Path("./inp_distribution.txt")
        if not inp_distribution.exists():
            raise FileNotFoundError("inp_distribution.txt not found in MC/inputs or top directory.")
    basics.inp_distribution = inp_distribution
    if stemcell:
        basics.pdir = Path(stemcell)
        prepare_one("", basics)
    else:
        for inp_file in basics.inp_files:
            prepare_one(inp_file, basics)
