This directory, `py_tests/Iss24` contains minimal data to
test the operation of `sum_results.py`.  

`test_sum_results.py`'s `test_shared_prefix()` uses this directory.
It first cleans out the results of the previous run, if any, and
then runs and tests the program.

Issue #24 describes the problem which this test reproduces.
The inputs here are radically trimmed versions of production
runs.

The directory is not suitable for runs of `montecarlo.py` or `runsims.js`
because it only has what the post-processing `sum_results.py`
requires.

If the test fails because it lacks permission to create `results/summary`
it may be that the parent directory `results` is set read-only. Uncheck that box
in the properties dialog for `results` from Windows Explorer.  It is likely 
that this problem is specific to `MS-Windows` and that `git` will not preserve
the necessary permissions.  It may well depend on other specifics of the setup
of the system and the user attempting the operation.  I encountered this problem
despite having sufficient permission to delete the directory, to create the
directory in `Explorer`, and having admin rights.
