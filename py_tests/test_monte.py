# test some of the python monte-carlo code
# Using pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(r"bin\python").resolve()))
from montecarlo import *

def test_inp():
    inp = InpFile(r"Mod92_MC-setup_Working-example\i25")

# if run under debugger
if __name__ == "__main__":
    test_inp()