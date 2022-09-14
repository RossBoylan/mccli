# test some of the python monte-carlo code
# Using pytest
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(r"bin\python").resolve()))
from montecarlo import *
import montecarlo

def test_inp():
    inp = InpFile(r"Mod92_MC-setup_Working-example\i25")

def test_effects():
    montecarlo.RG = np.random.default_rng([4, 89723509814])
    eff = Effects(ifname=r"J:\source\repos\mccli\Mod92_MC-setup_Working-example\inp_distribution_25mmHg.txt",
    ofname="test_effect.out")
    eff.print_labels()
    eff.print_data()

# if run under debugger
if __name__ == "__main__":
    #test_inp()
    test_effects()