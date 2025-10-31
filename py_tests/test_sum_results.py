import pytest

from pathlib import Path
import shutil
from subprocess import run
import sys

def test_shared_prefix(request):
    "perform a test for Issue #24 when one .inp name is a subset of another"
    # identify directories and files of interest
    test_dir = request.path.parent
    working_dir = test_dir / "Iss24"
    project_dir = test_dir.parent
    prog_path = project_dir / "bin" / "python" / "sum_results.py"
    MC_dir = working_dir / "MC"
    input_variation_dir = MC_dir / "input_variation"
    summary_dir = MC_dir / "results" / "summary"

    # actively setup test directory
    if summary_dir.is_dir():
        shutil.rmtree(summary_dir)
    # the next line has a nasty tendency to fail on
    # MS-Windows with a permission error, even though
    # I have admin rights.
    summary_dir.mkdir()
    # c. Python 3.14 Path.copy is defined
    shutil.copy2(input_variation_dir / "inp.orig.txt", input_variation_dir / "inp.txt")

    # run the command
    run([sys.executable, prog_path] , cwd=working_dir, check=True)

    # verify output is correct
    nLines = 0
    with (MC_dir / "results" / "summary" / "ageranges_TOT_MI.csv").open("r") as fcheck:
        for line in fcheck:
            nLines += 1
    assert nLines in (14, 15)  # 15 allows for the blank line at the end
    # clean up generated files skipped since they may help diagnose problem
    # The setup logic above blows the outputs away just before testing sum_results.py
