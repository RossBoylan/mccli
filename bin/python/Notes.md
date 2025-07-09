Notes on what files `montecarlo.py` uses.  Also files used by `runSims.js` and `Fortran`.
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

Parallel
========

Challenge: File Conflicts
-------------------------

To run more than one simulation at a time requires assuring the different simulations do not step on each other.  The obvious way this could be a problem is if they both write to the same file.

I ran the simulation under `procmon` to capture what files were being opened, read, and written.  This showed files in almost every directory--include ones with "input" in the name (!)--got writes, many of them to files that did not have an iteration number suffix.  Also, some of the `_mc0` file may be written repeatedly.

The one bit of good news is that I did not find any mystery files that were written only for the duration of the run, being neither an input nor an output.  I thought I saw such things in an earlier version of the source code.  Or perhaps there were such files, but the names did not stand out to me.

The conclusion is that, for safety, one must copy basically the entire directory.

Challenge: Interactivity
------------------------
The monte-carlo system assumes it is running in a regular terminal with a person who can respond to prompts.  This makes it awkward to run multiple copies.

This is most obvious for `mc init`, whose primary job is to collect user input.  It does this with a curses-like interface that uses multiple rows of the terminal and allows one to scroll through alternatives.  The "solution" is to run this *before* the parallel run.

However, `mc run`, the main simulation driver, also assumes and requires such an environment.  If it encounters signs of a previous run, it asks the user what to do.  And its logging procedure has commands like `clearLine()` and `cursorTo()` that only work with a terminal.  When I ran the program with a pipe for `stdout` that same call produced an error, because the output object did not understand the command.  In `node` the stream does have an `isTTY` attribute which could be checked.  Solutions are

  1. Provide an `--overwrite` option that will suppress the query if there seems to be a previous run, acting as if the user selected overwrite the existing results.  This is risky.
  2. Provide a `--json` option which simultaneously produces `json` output and avoids any terminal manipulation commands.

Challenge: Subprocess Management
--------------------------------
To run in parallel, each simulation must run in its own process and its own directory.  Using threads is possible in principle, but `python` threads are ineffective because of the global lock.  And threads are messy anyway. While I could create separate python processes, that adds an unnecessary extra layer to the invocation of `node`.  The most effective way to deal with multiple long-lived processes is to use the `asyncio` module and coroutines to launch the different runs.

### Capturing output as it occurs

A perennial weak spot in `python` is getting output from a subprocess while it runs, rather than having to wait until it completes.  That output has progress reports, and so is essential for monitoring progress.  The advice in the documenation is to use `communicate()` to avoid deadlocks, but, as the documentation says, this only returns after the process exits.

I fond various questions about this problem but not a lot of solutions.  One suggestion was to use `readLine()` on the file handle (pipe), which worked for me once I ensured `\n` was written at the end of output lines, and once I added a rather cumbersome `asycio.Task`-based approach so I could wait on `stdout` and `stderr` separately.

In practice, it seems both tasks complete at once, even though the `stderr` reader returns a 0-byte result.

There are alternative methods of communication: shared memory, named pipes, other IPC frameworks (I considered `RabbitMQ`), even reading from a file as it is written.  But pipes seemed lightest weight and most straightforward.

### Sub-subprocess output

`runSims()` is the `mccli` `javascript` function that runs the simulations.  It invokes other processes, `python` and `Fortran` programs.  So even if the main `node` code sends everything as a `JSON` message, there may still be traffic directly to `stdin` and `stdout` that it does not control.  The `javascript` function `runSims()` attempts to capture subprocess output and convert it to `JSON`.  `maestro.py` captures both `stdout` and stderr`, separately, and attempts to recognize non-`JSON` output and convert it to `JSON`.

### `JSON` format

Every `JSON` message should have `type` field at the top level.  Here are the current values:

  * `PROGRESS` reports on progress for individual iterations.  One is issued at the start of an iteration, and another, with more information, is sent at iteration end.
  * `SUMMARY` after all iterations complete
  * `DETAIL` details of all simulations
  * `DONE` very last message
  * `ERR` error.
  * `INFO` various informational messages
  * `ARGS` arguments passed to `runSims()`
  * `DETAIL` details about the entire run, emitted once at the start and once at the end.  Also written to `MC\results\.run`.
  * `SUMMARY` start and end of the `sum_results.py` run after all iterations complete.
 
 All have a `text` field with the main message and some have additional fields.  See code for details. 




Challenge: `asyncio`
--------------------

`asyncio` is a solution that introduces its own problems.

### `Qt`

`Qt` has an event loop.  But `asyncio` has its own event loop.  They can only get along with some help.  `Qt` has a `QtAsync` module that allows the `Qt` event loop to also serve as the event loop for the `python` `async` calls.

The architecture of coroutines in `python` is a little odd.  The language definition defines some keywords, `async` and `await`, and the semantics they should have.  But it does *not* provide the mechanism so they can actually run!

The `asyncio` standard module does provide such a mechanism, but it is not the only way to achieve the task scheduling required for cooperative multitasking.  So other packages can and do provide such services.  `Qt` does so on top of `asyncio` so that code will actually use both `QtAsync` and `asyncio` modules.

*However* `QtAsync` is only available for `Qt6`, and only barely:
"[This module is currently in technical preview](https://doc.qt.io/qtforpython-6/PySide6/QtAsyncio/index.html)" as of 2025-06-15.  It seems to be available only with recent version, perhaps `Qt6.8+`.  And that in  turn limits the supported `python` versions.  Apparently 6.8 requires `python3.9` and 6.9 requires `python3.10` according to the underexplained [python compatibility matrix](https://wiki.qt.io/Qt_for_Python).

`python` support for `Qt6` is from the `pyside6` module, *not* the `pyside2` this package currently uses in `frmtReport.py`.  So using both requires 2 heavyweight installations.

`frmtReport.py` could be ported to `pyside6`, but that would take some time.

Another consideration is that `pyside6` is not obviously available as a package on stable Debian or Ubuntu (June 2025).

### `SQLite`

Since this is the database used by `frmtReport.py` and the new heart-failure code, it seems natural to use it here.  But it's synchronous, and doesn't naturally get along (may even refuse to run) with `async` settings.

There are once again some packages designed to smooth the differences.  In fact, `pyside6` has a local storage option built on `SQLite`, as well as more general database interfaces.  Using that, if I'm using `Qt` anyway, might be simplest.

Persistence
-----------

The overall system writes lots of information to regular files, and a some key facts about the run to `MC/results/.run` as JSON on completion.  There are 3 motivations for the parallel processing itself (`maestro.py`) to use persistence:

  1. If processing is interrupted it can serve as a checkpoint for restarts.  It can also indicate exactly how the work was carved up: did individual runs include multiple `.inp` files?  Did individual runs cover only part of the range of iteration?
  2. The log of all messages received will be large.  Even if they could all fit in memory, it's wasteful to store them that way.  There will be too many to fit on the screen, and so if something goes wrong it will be useful to have a record of what they were.
  3. Storing the messages in a database allows the use of database queries to extract information; potentially these can use indices to speed up retrieval.  They can also work with GUI frameworks for efficient display of big data without showing it all.

Counter-arguments, using the same numbering as above:

  1. There is currently no resume capability.  If there were, it could be implemented by scanning for output files to determine how far the simulation got, although that could be fooled by previous runs if they were left in place.  While there is no good way to determine how the runs were split up, that information could be written to a small text file.  And, currently, there is no choice about how to split things up.
  2. There probably is enough RAM to hold all the messages.  They could be written to a plain text file in case of disaster, with manual examination of the file to find old messages about failures.
  3. I can use indices without persistence.  The availability of good database-friendly GUI's seems a bit spotty: it's unclear to me if `QtQuick` offers such a framework.

Most of the messages are in `JSON`, which is irregular (not fixed rows and columns).  Both `Postgres` and `SQLite` have `JSON`-specific types that can be used for storage and queries, which are thus not exactly regular `SQL` queries.

As noted just before this section, there are challenges to using databases with `async` code, and perhaps with other event loops as well.

Matrices of Time
-----------------

The underlying `JavaScript` monte-carlo code stores time as milliseconds past the epoch (start of 1970), and durations as milliseconds.  It sometimes  convert these to various printable forms, using Los Angeles as the time zone.  Since I want to compute expected completion for the entire batch, and perform other timing calculations too, the question arises how I should store it.

I'll use matrices of iteration x run, where run is a single batch of simulations, indexed by integer.  They may have start, end, or duration times.  To reduce footprint (relative to `pandas` or `scipy`) I'll use `numpy`.  I will store times as 64 bit integers, and only convert to human form just before presentation.  And I will use `np.nan` for values not set yet.

`numpy` has datatypes `datetime64` and `timedelta64`, corresponding to `Python`'s `datetime.datetime` and `datetime.timedelta`, and so it seemed natural to use them.  But the handling of missing values was problematic.  Both types have an instance know at `NaT` for "Not a Time" for missing values, and these appear to propagate as one would hope.  But that means a sum (I tried) or mean (I presume) will be `NaT` if any of the components are.  `numpy` has a bunch of `nan*` functions that calculate *after* dropping missing values; they do not appear to work `NaT`, as opposed to `np.nan`, for which they were designed.

One could either compute an approprite mask on the fly, or just use the known to be good subset of the data.  At least for my initial case, that's pretty easy to track.  But that is both programming and execution time overhead.

Another option is to use `numpy.ma` for "masked" arrays, which have a separate boolean matrix indicating which cells of the data matrix are invalid.  The `numpy` [website](https://numpy.org/devdocs/reference/module_structure.html) counsels against their use: "Prefer not to use these namespaces for new code. There are better alternatives and/or this code is deprecated or isn’t reliable.".  The masked array namespace is described as "not very reliable, needs an overhaul".  I don't see any specific suggestion of what to use instead.  I take them at their word and avoid it.

That leaves me with integer matrices that have `np.nan` for (currently) unknown values and the `nan*` functions for summarizing them.  **But it doesn't work. `numpy` has no integer `NaN`.**

`pandas` has `NaT` time values, and supposedly they are handled as other NA's are. But the **best solution seems to be to record time as seconds**, a `float` value = time from `javascript`/1000.  This is also easier for human interpretation.

  * Division by two integers, even 1/1, yields a `float` in `Python`.
  * Double precision floating point, which it uses, has 15-17 decimal digits of precision.
  * The current time in milliseconds is 13 digits.  So there should be no loss of precision.

It's unclear to me exactly how time zones interact with the millisecond value.  3 AM here is currently 10 AM UTC; I'm not sure if the milliseconds value is til 3 or 10.  `numpy` time types are not aware of timezones.

There are all kinds of subtleties with time, including leap seconds. `numpy` says it follows the Unix convention of treating every minute as 60 seconds.  Real clocks have leap seconds added from time to time (~ a few times in a decade).  And there are the complications of timezones and daylight saving, which might make naive times skip forward or back.  And there are differences in the range of dates that are representable, or considered valid (e.g., use of Gregorian dates before the calendar was introduced.)  The precision may also vary.



Log
===

2022-09-14
----------
Modified test code to write out iteration number.

To Do
=====

  - [ ] Parallel Runs w/maestro.py
    - [ ] TerminalTimerLog
      - [x] errors when all NA
      - [x] Never completes
      The final iteration was not sending a `PROGRESS` message at the end, and so `maestro.py` never found iterations remaining to 0.
      - [x] Report completion immediately, rather than waiting for `_delay`.
      - [ ] Bias throughout the run because quick jobs finish sooner.
      I "dealt" with this for iteration 1 with a warning message.
      - [ ] Races?  I think I'm OK because actually single-threaded.  E.g.,
        - [ ] _dirty flag reset during a report.
        Definitely an issue while in debugger.  Dealt with by moving 
        clearing the flag to the top of the `report()` function.  With real
        multithreading the flag might be dirtied before report() finished its
        calculation.  But that would only lead to an extra report when nothing
        had changed.
        - [ ] inconsitencies within calculations
        E.g., something might be updated between calculating iterations remaining
        and time remaining.
        - [ ] `async` is not an absolute guarantee of safety; computations can still
        be interleaved whenever they yield control, and the yield (`await`) could
        be hidden in a function called by the function one is considering.
    - [ ] External review of `maestro.md`
    - [ ] Extend to parallelizing within a single `.inp` file, i.e., by iteration
    - [ ] Extend to allow multiple `.inp` in a single run.
    - [ ] GUI
      - [ ] raises issues with the event loop.  GUI frameworks have their own.
    - [ ] database
      - [ ] to save messages for a single run.
      - [ ] the messages would most naturally be saved and searched as `JSON`.
      - [ ] to save information on multiple runs
      - [ ] also raises event loop issues, at least for some db's.  `SQLite` is
      allergic to `async`.
    - [ ] review notes in the Parallel section above for to-do's
    - [ ] review maestro.md for to-do's
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
