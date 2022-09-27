Change Log for `mccli`
3.3.0 2022-09-27 ross.boylan@ucsf.edu
    * .inp file distribution parameters now interpreted as mean and std dev of the generated
    variable.  This was supposed to have been true already, but it wasn't.  
    Partially addresses [RossBoylan/mccli#4](https://github.com/RossBoylan/mccli/issues/4) but
    note it affects *all* non-Normal distributions.
    * Add a python test harness using pytest in the py_tests directory.  It is not hooked into
    javascript testing, which remains non-existent.  Partially addresses [RossBoylan/mccli#12](https://github.com/RossBoylan/mccli/issues/12).
    * Internal changes:
       + Allow overriding the default files assumed many places in montecarlo.py. 
       This was done to permit the white-box tests I wrote, but could in principle be
       exposed to the user.
       + Notes.md has various notes, currently focused on montecarlo.py, how it works,
       and what needs to be done.
  
3.2.0 2022-09-12 ross.boylan@ucsf.edu
    * Use 8 digits after decimal for quantities varies in .inp files.  Was 6.  Closes #19.
    * Update a help message and requirements to match current situation.

3.1.0 2022-08-13 ross.boylan@ucsf.edu
    * Rely entirely on new features of `NumPy` for parallel random number generation.
    * Drop use of `randomgen` Python package.
    * Resolves #18 triggered by failure of our code to work with current `randomgen`.
    * Further emphasize the wisdom of specifying a seed.
    * Drop fuss over `randomgen` and `NumPy` versions in `README.md`.
    * Extensive changes to installation instructions in `README.md`, which now instruct the use of virtual environments.
    * Clarify interactive question about existing results.
    * Use real math in `README.md`.
    * Fix missing `np.` qualifier in code.
    * Pin `Node` package `inquirer` to avoid its shift to ESM format in version 9.  Would require extensive code changes.
    * Stop attempting to auto-install python packages when `mccli` (which is a `Node` package) is installed.  The auto-install only worked on MS-Windows and didn't respect python virtual environments.
    * These are changes since 3.0.1 on 2022-02-03 with hash 1c93968a63c0685b6cac54505343eed50804cabd
  
  