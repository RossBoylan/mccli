Change Log for `mccli`
* 3.5.0
  * Add `maestro.py` to run jobs in parallel automatically.  Do *not* use without
  checking that it is using the intended directories.  You should launch it from the 
  project/data directory top level *after* having run `mc init` and done the file setup
  it suggests.  See the "Parallel" section in [notes](bin/python/Notes.md) for more.
  * Add `maestro.md` documenting the use of the program, and material in `Notes.md` about
  implementation.
  * Add `--json` and the dangerous `--overwrite` options for `mc run-sims`. These 
  are intended for use by another program that controls the `mc` program.

  The remaining changes are  not tied to parallel runs.

  * Remove pin of `inquirer`, a `node` module, to an old version as recent
  versions restore packaging for traditional (CJS) modules.  Remove related installation
  instructions.  However, the pin removal was only partly effective; it is still locked
  to the old v8.
  * Add `my.ps1`, a sample `PowerShell` setup script.  You will need to customize it so
  that it moves to your project directory as the last step.  This sets up abbreviations
  for running `mc`.

* 3.4.0 2025-04-02 ross.boylan@ucsf.edu
  * Support new .dat format for HF model (qol and shrt)
    Previous version induced correlations between variables we want to consider
    uncorrelated. E.g., for qol the values for `1-Ang`, `11-MI` and `21-AngHF`
    were all in lockstep.
  * Do *not* use this with the old Fortran model
  * Untested.

* 3.3.2 2022-10-18 ross.boylan@ucsf.edu
    * Fix: beta distribution can't handle vectors
    ```
        File "J:\source\repos\mccli\bin\python\montecarlo.py", line 594, in _correlated_beta
          alpha, beta = mean_to_native("beta", ms, ss)
        File "J:\source\repos\mccli\bin\python\montecarlo.py", line 170, in mean_to_native
          r = beta_native(means, sds, check)
        File "J:\source\repos\mccli\bin\python\montecarlo.py", line 222, in beta_native
          if sds**2 > means*(1-means):
      ValueError: The truth value of an array with more than one element is ambiguous. Use a.any() or a.all()
    ```
      
    * Revise documentation to better match current behavior.

    * Implementation Changes
      + add tests for beta distribution
  
* 3.3.1 2022-10-04 ross.boylan@ucsf.edu
    * Fix errors in `.dat` file processing induced by new code in some circumstances.  In `montecarlo.py`:
      ```
            >   			res[mask] = stats.lognorm.ppf(np.full(sum(mask), q), s = sigma[mask], scale = np.exp(mu[mask]))
            E      TypeError: 'bool' object is not iterable
      ```
        The cause was the return value conventions from the new `mean_to_native()` routine; singletons were no longer returned as arrays, violating expectations in the DatFile code.
        The fix is to strip the array away more selectively, only if there are no dimensions.
    * Fix errors in handling illegal parameter inputs (exposed when others are fixed)

    * Implementation Changes

      + Modified `DatFile` and `SDFile` to facilitate testing by overriding their default inputs and outputs.
      + Added `test_dat()` to test them
      + Provided input test data

* 3.3.0 2022-09-27 ross.boylan@ucsf.edu
    * `.inp` file distribution parameters now interpreted as mean and std dev of the generated
    variable.  This was supposed to have been true already, but it wasn't.  
    Partially addresses [#4](https://github.com/RossBoylan/mccli/issues/4) but
    note it affects *all* non-Normal distributions.

    * Internal changes:
       + Add a python test harness using pytest in the py_tests directory.  It is not hooked into
    javascript testing, which remains non-existent.  Partially addresses [#12](https://github.com/RossBoylan/mccli/issues/12).
       + Allow overriding the default files assumed many places in `montecarlo.py`. 
       This was done to permit the white-box tests I wrote, but could in principle be
       exposed to the user.
       + `Notes.md` has various notes, currently focused on `montecarlo.py`, how it works,
       and what needs to be done.
  
* 3.2.0 2022-09-12 ross.boylan@ucsf.edu
    * Use 8 digits after decimal for quantities varies in  `.inp` files.  Was 6.  Closes #19.
    * Update a help message and requirements to match current situation.

* 3.1.0 2022-08-13 ross.boylan@ucsf.edu
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
  
  