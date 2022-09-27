# test some of the python monte-carlo code
# Using pytest
from math import sqrt
import numpy as np
from pathlib import Path
from scipy.stats import chi2
import sys
sys.path.insert(0, str((Path("bin") / "python").resolve()))
from montecarlo import *
import montecarlo

rootDir = Path(".").resolve()  # top mccli directory
testDir = rootDir / "py_tests"

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
    inp = InpFile(str(rootDir / "Mod92_MC-setup_Working-example" / "i25"))

def test_effects():
    iter = 4
    montecarlo.RG = np.random.default_rng([iter, 89723509814])
    eff = Effects(ifname=str(testDir / "inp_distribution_25mmHg.txt"),
    ofname=str(testDir / "test_effect.out"))
    eff.print_labels()
    # Ordinarily runSims.js writes the iteration number to the file
    # I think this achieves the same format.
    eff.save_write("{:<18d}".format(iter))
    eff.print_data()

def test_component():
    # If there is no group specification then the state of the RG
    # is not restored, which allows us to test the results of
    # a series of draws.  If we specified the group we would just
    # get the same number over and over.
    i = 0
    montecarlo.RG = np.random.default_rng([i, 89723509814])
    # omitting the distn should give the normal
    #dists = [None, "LogNormal", "Beta", "Gamma"]
    dists = [None, "Gamma"]
    mu = 20
    sigma = 4.3
    # comments already stripped out by time input line gets to Component
    params = f"{mu}, {sigma}"
    nrep = 800
    # So far I use matrix v one column at a time, i.e., unnecessary
    v = np.zeros((nrep, len(dists)))
    distj = 0  # index of distributions

    for d in dists:
        if d:
            comp = Component(f"{d}, {params}")
        else:
            comp = Component(params)
            d = "Normal (implicit)"
        for i in range(nrep):
            v[i, distj] = comp.sample()
        m_samp = v[:, distj].mean()
        # next test fails at the outer
        assert sqrt(nrep)*abs(m_samp - mu)/sigma < 2.5 , \
            f"{d} sample mean {m_samp} is too far from true value of {mu}"
        # get quantile for sd
        var_samp = v[:, distj].var()/(sigma*sigma) # normalized variance
        var_q = chi2.cdf((nrep-1)*var_samp, nrep-1)
        # following test fails at the outer 1.4% of the distribution
        assert abs(var_q - 0.5) < 0.493, \
            f"{d} sample sd {v[:, distj].std()} too far from true {sigma}. p={var_q}"
        # that should also catch the degenerate case in which var=0
        # because same seed is being reused
        del comp

        distj += 1

         


# if run under debugger
if __name__ == "__main__":
    #test_inp()
    test_component()