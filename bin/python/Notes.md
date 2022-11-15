Notes on what files montecarlo.py uses.  Also files used by runSims.js and Fortran.
So probably I should move this file to a different directory.
This is to aid testing.

Also includes info on tracking failures.

# Notes on Internal Use of Files
`montecarlo.py` reads an input file (or is it a dat file?) from `_mc0.<ext>` and writes to `_mc.<ext>`.  The javascript code copies the _mc to a numbered version, but that is strictly for archival purposes; the Fortran model will use the _mc file.

The input files `${inp_files[j]}_mc.inp` are not renamed; they are specified as inputs to the fortran model on the command line via shell redirect.
These input files are manually modified at the start to select xx_mc.dat files for the appropriate parameters.  The input file just has a number selecting an entry in a .lst file.  The .lst file is also modified manually.  See the instructions above in the "Modfile setup" subsection for this.

It looks as if the varied files are written to the same spot as the inputs, i.e., _mc are written next to the _mc0 files.  *So the python code also has the embedded assumption that just one simulation is happening at once.*

`Modary.f90` line 157 begins definition of files for b (`filename(7)`) and `copy input\b'//rfn//rfk//'.dat modfile\b.def`. I guess `rfn` and `rfk` (defined in `main.f90` @151; `rfn` is set either to `6` in `Modarray.f90` or, I think, in a weird write statement in `addrfs.f90`@159 `WRITE(rfn,'(i1)') irft`) indicate what type of riskfactors were chosen.  Example source files are `B6SBD.DAT` and `B8SPKpool.DAT`.

`Modary.f90` @441 resets `filename(7)` with the selected entry in the list, if you have said you want to modify it.

`Subs.f90`@1070 `picfile()` allows user to select from list retrieved from an inputlst file in `modfile\`.  That's `b.lst` in this case. *If* the file has more than one alternative, ask user which to pick.  The name of the selected file is set in the `filname` argument, known as `tmpfile` in the caller.  Then copy `modfile\<selected name>` to a temp file `utils\zzzCHDedit.tmp`. *This is another move that will fail with parallel runs.*  Resets the name in `filename(7)`. User gets chance to edit it and I think it ends up with the regular name.  `Modary.f90`@460 calls `initial` with `b` the first argument.

`init.f90` defines that subroutine at the top.  It reads in the b coefficients from `modfile\` starting at line 426.  Writes the input matrix as text to `input\inputchk\b.def` as a way to allow a check by a person that the input was read OK.

The `b` array is defined in `module modelarrays`.  Although `initial()` does not use the module, using function arguments instead.  Fortran is generally call by reference.

Here's a list of the inputs and outputs mentioned explicitly in `runSims.js`.  It does *not* include all files the python programs or the Fortran model read and write.

| Read                                        | Write                          |
|---------------------------------------------|--------------------------------|
| MC/inputs/input_data.json||
| MC/results/cumulative (test for prior run) | MC/saved_runs/XXX (copy results and input_variation)|
|                          | MC/results  (emptyDir)|
|                          | MC/results/{breakdown,cumulative,summary}|
|                          | MC/input_variation (last emptyDir)|
| /usr/bin/python          ||
| MC/input_variation/inp.txt (optional)|MC/input_variation/inp.txt (iteration number)|
|operation of python program | happens here for dat files|
| modfile/dat_file_mc.dat   | MC/input_variation/dat_files/dat_file_NN.dat (copy)|
| (only if previous name > 12 chars)| modfile/truncated name (link)|
| inp_file_mc{,0}.inp       | inp_file_mc.out (delete)|
| CVDIntel9.2exe (with inp_file_mc.inp)| MOD_zerorun.txt (iteration 0 only)|
| format.py  inp_file_mc.out  | inp_file_mc.frmt|
| inp_file_mc.frmt          | MC/results/breakdown/inp_file_NN.frmt|
| outfile.dat               | MC/results/cumulative/inp_file_NN.dat|
| sum_results.py (when all done)||
|                           |MC/results/.run|


# Other Notes

Command line from runSims.js usually has `-s` (save outputs), `-i` and `--seed` but no file names or directories.  Looking through the code, it seems `-s` only matters for outputs of the zero run.

I don't know where, but something seems to clear out `inp.txt` at the start of a run.  I ran after having done a preliminary run that produced `inp.txt` with headers and an initial line.  After the run started there was no sign of duplication.

`MC/inputs/input_data.json` read to find what to vary.  Use lists in 2 sections, 'dat_files' and 'inp_files'.  For 'dat_files' the zero run (`-z`) does nothing except write the data out.  For 'inp_files' the zero run writes out labels.  Both execute `vary()` on the file object and then `print_mc()`.

`VFile(fname)`
    `pref,ext = fname.split('.')`
    input: pref+'_mc0.'+ext
    output: pref+'_mc.'+ext

It reads from an `_mc0.EXT` file and writes to `_mc.EXT`.

`DatFile` includes an `SDFile` but `InpFile` includes `Effects`.
    `DatFile(file_data, random_generator)` where `file_data` is a `JSON` structure
    that include 'filename' -> `modfile/FILENAME.dat` as primary input (for `VFILE`).

`InpFile(fname)` calls `VCFile(fname+'.inp')` and then creates
    `Effects` which has no arguments.

`Effects` reads from `MC/inputs/inp_distribution.txt`.
    Writes to `MC\input_variation\inp.txt`.
    Uses `Component` in a transitory way to wrap some lines.
    This javascript code in `runSims.js` actually fills in the iteration number which is the first field on the data lines:

   ```javascript
        let str = String(i + ' '.repeat(16));
        let INP_OUTPUT_FILE = './MC/input_variation/inp.txt';
        if (fs.existsSync(INP_OUTPUT_FILE)) {
            fs.appendFileSync(INP_OUTPUT_FILE, str.substring(0,16) + '  ')
   ```

`Component` actually generates the random number and interprets 
    parameters.  It would probably be better to generate them once and retain them.
    Although `Component` instances are temporary, there is persistent state held in a class variables.  This is the state of the random number generator for each group.

Note that `montecarlo.py` is only used to generate a single simulation.  Because of the state-keeping in `Component` it would actually generate the same numbers if called again.

An effect may be made of several components that are summed or added to the mean.

2022-09-13 Start `issue12` branch to fix random number generation with LogNormal .inp files.
Initial focus on being able to run tests.  Create `py_tests` folder at very top level to use the pytest framework, and configure `VSCode` for same. Created `test_monte.py` and, after painful experiments with getting it to load the code, made a simple test work.

Further testing of `Effects` revealed 2 different ways the code was inconsistent with the current `numpy.random` interface:
  1. The state has moved to the `BitGenerator` and is not directly accessible.
  2. `randn` is obsolescent (it is still available, but not through the old interface).
Fixed both.

Sampling for .inp and .dat Files
================================

The code handling random number generation for .inp files, in `InpFile`, `Effects` and `Component` is almost completely separate from that for .dat files in `DatFile` and `SDFile`.  This results in numerous differences, some intentional and some not (e.g., interpretation of parameters for the same distribution differs between .inp and .dat.)

Our current code for the .dat file simulations does not handle Gamma (or possibly treats it as Normal).

Since it would be good to put the code for each distribution in one place, it would be good to resolve this inconsistency, even though there are currently no gamma parameters in the .dat files.

Other notable differences between .dat distributions and .inp distributions
1.	The user never specifies the type of distribution for .dat files; it is wired in to the definition of the variables in the code.  For .inp files the user does set the distribution (often by omission, which means normal).
2.	The .dat distribution is set per parameter in bin\input_data.json and none are gamma.
3.	Likewise, the .dat correlation structure is defined with the variable and may be block or row.  User doesn’t set it.  
4.	The .inp correlation structure differs from that for .dat, and is user-defined by groups.
5.	.dat defines the mean and sd in 2 separate files. .inp defines the distribution parameters in one file.
6.	For .inp, but not .dat, one can specify max or min values for the generated samples.
7.	.inp allows “MEAN” to be given as the mean, in which case the second parameter is taken to be a coefficient of variation around the original mean (I think?).  I don’t think that’s an option for .dat.
8.	The .dat file has a bunch of special rules to handle “illegal” values of the beta parameters.  Negative means flip the sign  of the result from the corresponding positive mean, and sd <= 0 result in always drawing the mean value.  .inp files get no such rules.
9.	.inp files allow you to specify multiple components, all of which are summed to give the parameter of interest. .dat files don’t.
10.	.inp files attempt to achieve random number correlation by matching seeds; .dat files do so by matching quantiles.

Getting Error Info from Python
==============================
When `montecarlo.py`, invoked from `runSims.js`, fails, very little information gets back, just a message "montecarlo.py run failed".  This is unhelpful.  Neither the exact call used to invoke the python program nor the traceback for the error or console output (if any) is available.

Some of this stems from the use of `{silent:true}` option, which is the default, for the invocation of `shelljs` (which is the module name, even though aliased to `shell`).  Apparently the return value for a syncronous call is a `ShellString`.  See https://github.com/RossBoylan/mccli/issues/20#issue-1443014991 for more.

The `python-shell` module advertises much better error reporting, but I've never been able to get it to do anything.  My latest attempts apparently couldn't even get it to run anything.  I have *2* different branches experimenting with the package, *both* named `python-shell`.  The primary archive in `J:\source\repos\mccli` has that branch with work from Feb 2022.  The archive in `C:\Users\rdboylan\Documents\KBD\mccli-release`, intended for production runs, has some *different* work from Nov 2022.  It is not based on the earlier branch.

Log
===

2022-09-14
----------
Modified test code to write out iteration number.

To Do
=====

  - [x] Analyze input and output files for `montecarlo.py`.  See above.
  - [x] Pick a testing framework: `pytest` (only alternative in `VSCode` is the older `unittest`)
  - [x] Incorporate montecarlo module into it.  Remarkably undocumented how to do so.  Done by supplementing `sys.path` and using `import`.  Needed one import to get the names at top level, and another to get the module accessible for messing with its global state.  The working directory, at least when I run the test code in the debugger, is the top level project directory.
  - [x] Modify key classes and functions to allow me to override the default file name conventions.  Done for those involved with `InpFile`.  See below for `DatFile`.
  - [x] Eliminate some hard coding of path separators
  - [x] Write first tests, including setup of test framework in `VSCode`.
  - [x] Fix breakage from interface changes in `numpy` for the code in `Component`.
  - [x] Identify why there is no simulation number on outputs from first tests of `Effects`.
  - [x] Test writes out iteration number to `Effects` output file
  - [x] Find out if the way I'm saving and restoring state is effective.  It is.
        In particular, should I be doing a deep or shallow copy? Neither is necessary; it's already a copy.
        https://github.com/numpy/numpy/issues/22337 created 2022-09-25; the answers incorporated into this item.
  - [ ] Add a test for the  correct operation of save/restore state (maybe)
        Likely tied to implementation details, which I may be about to change.
  - [ ] Make argument and instance variable naming more consistent across the module for input and output files (maybe)
  - [ ] Make handling of file closing more consistent and correct.  
    Sometimes I do, and sometimes I don't.
    Inconsistent and confusing.
    This has 2 dimensions: handling of filelike vs pathlike arguments, and handling across different classes and methods.
  - [ ] Move all test input files into project source tree under `py_tests`.
  - [ ] Is it OK to publish the test data?
  - [ ] Complete tests for `Effects` as is.  In particular
    + [  ] test values are reasonable given mean and sd
    + [  ] values are in expected domain (maybe)
    + [  ] correlation pattern as expected
    + [  ] fails when given invalid specs
    + [  ] works for all distributions
  - [ ] Add tests for Effects with multiple iterations.
        Requires properly reseting global state of `RG` and `Component.group_state`
  - [ ] Test `InpFile`
  - [x] Recreate failure of LogNormal for `.inp` (using `Component`, the core of the problem, but not a high-level test)
  - [x] Correct failure of LogNormal in main code
  - [x] Update package version and changelog
  - [x] Reintegrate with main `repeatable` branch
  - [x] Publish changes
  - [x] Extend flexible specification of inputs and outputs to `DatFile`, `SDFile` and other related classes and functions.  This might be good to do before publication, in case I broke something.
  - [ ] Centralize random number logic in one place.  Currently both `InpFile` and `DatFile` have independent code.  Unclear how feasible this is since they have different types of correlations they are trying to achieve, and different sets of special rules. (maybe)
    + [x] transform from mean and sd to distribution parameters now done centrally
    + [ ] see list above (Sampling for .inp and .dat Files) for differences
    + [ ] handling of out of bound inputs
      * [ ] check LogNormal
            Modified to compute params from mean and sd only for legal values
            and then use those legal parameters with an appropriate mask
            Check that it all done properly in all places.
      * [ ] Problematic because the current specification gives special handling to out of bounds values for only .dat or only .inp files in some cases, as noted in previous section.
      * [ ] check handling of illegal values for other distns, including Normal, to see if it has a similar structure.
  - [x] beta distn fails when it gets a vector
      Monday, October 17, 2022 7:19:01 PM
      ERR montecarlo.py run failed
      Traceback (most recent call last):
        File "J:\source\repos\mccli\bin\python\montecarlo.py", line 963, in <module>
          main()
        File "J:\source\repos\mccli\bin\python\montecarlo.py", line 41, in main
          datfile.vary()
        File "J:\source\repos\mccli\bin\python\montecarlo.py", line 306, in vary
          self.vary_line(line_num)
        File "J:\source\repos\mccli\bin\python\montecarlo.py", line 373, in vary_line
          varied = self.sdfile.get_variation(line_num)
        File "J:\source\repos\mccli\bin\python\montecarlo.py", line 609, in get_variation
          return self._do_line(line_num)
        File "J:\source\repos\mccli\bin\python\montecarlo.py", line 639, in vary_by_block
          return self._do_dist(self._rnd[block_num,], means, sds)
        File "J:\source\repos\mccli\bin\python\montecarlo.py", line 594, in _correlated_beta
          alpha, beta = mean_to_native("beta", ms, ss)
        File "J:\source\repos\mccli\bin\python\montecarlo.py", line 170, in mean_to_native
          r = beta_native(means, sds, check)
        File "J:\source\repos\mccli\bin\python\montecarlo.py", line 222, in beta_native
          if sds**2 > means*(1-means):
      ValueError: The truth value of an array with more than one element is ambiguous. Use a.any() or a.all()
  - [ ] In particular, `InpFile` should use the new, percentile-based logic to achieve correlation, instead of unreliable use of internal random generator state.
  - [ ] Allow specification of log-normal parameters the old way (on the log scale) (maybe)
  - [ ] Allow specification of truncated distributions; current code does censoring, bringing extreme values in to the boundary. (maybe)
  - [ ] Incorporate my fuller understanding of correlations in `.inp` files into user documentation.  Currently quite a bit is in this file and in comments in `montecarlo.py` (low)
  - [ ] Incorporate relevant material from https://github.com/ecfairle/CHDMOD into this project (may already be in our `README.md`) and eliminate reference to it in documentation and code (e.g., `montecarlo.py` has a comment referring to it.) (low)
  - [ ] Allow resuming after interrupted run from, e.g., system shutdown.  See issues #5, #2.
