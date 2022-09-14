# test some of the python monte-carlo code
# Using pytest
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(r"bin\python").resolve()))
from montecarlo import *
import montecarlo

"""
These are white-box tests of montecarlo.py.

That is, they use knowledge of what happens inside the code in order
to test components of it without doing an entire simulation, or even
an entire run of monte-carlo.py.

The benefits are much more precise, targetted tests with greater speed.
The drawbacks are tight coupling with the original code and the possibility
that the tests may fail to exercise the precise sequence and environment found in production 
runs.  Also, the underlying code became more complex in order to support the testing;
however, that complexity introduced additional features (mostly more flexible
specifications of inputs and outputs) that may be useful outside of testing.

Note that the montecarlo module maintains some global state, both at the top
level, e.g., RG is the random number generator, args holds arguments, and at the 
class level, particularly the Component.group_state class variable, which make testing
hazardous.  Also, runSims.js writes at least part of the line for one file, the Effects
output file, usually MC/input_variation/inp.txt. 

"""

def test_inp():
    # currently mostly used to see if montecarlo module loaded
    # it fails because input files are missing
    inp = InpFile(r"Mod92_MC-setup_Working-example\i25")

def test_effects():
    iter = 4
    montecarlo.RG = np.random.default_rng([iter, 89723509814])
    eff = Effects(ifname=r"J:\source\repos\mccli\Mod92_MC-setup_Working-example\inp_distribution_25mmHg.txt",
    ofname="test_effect.out")
    eff.print_labels()
    # Ordinarily runSims.js writes the iteration number to the file
    # I think this achieves the same format.
    eff.save_write("{:<18d}".format(iter))
    eff.print_data()

# if run under debugger
if __name__ == "__main__":
    #test_inp()
    test_effects()