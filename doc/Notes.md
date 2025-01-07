These are internal notes for developers:  
   1. [General](#general-notes-for-contributors) Orientation to those wishing to build or modify the source code.
   2. [What files](#notes-on-internal-use-of-files)  `montecarlo.py`, `runSims.js`, [stuff](#literate), and the `Fortran` model use; the motivation is to support testing.  This is *not* an exhaustive list of all the files used by the `Fortran` model.
   3. [Heart Failure](#heart-failure) (likely duplicates what's in User Guide)
   4. [Other](#other-notes) Notes on operation of simulation
   5. Notes on the [design of random sampling](#sampling-for-inp-and-dat-files), namely that sampling from `.inp` and `.dat` files uses different code paths and logic.
   6. Information on tracking [failures](#getting-error-info-from-python) from `Python` back to `JavaScript`
   7. [Log](#log).  Not much here, but this is where to record internal changes.
   8. [To Do](#to-do).  Use in conjunction with the issue tracker.

# General Notes for Contributors

See the [README](../README) for instructions on installing and using this package and the [User Guide](UserGuide) for additional information and background.

At the outer level this is a `JavaScript` package designed for `Node.js` to carry out simulations of an external `Fortran` model with externally provided data, in the form of many input files.  `mc` is the name of the top-level program. Significant parts of the work are performed by `Python` programs, mostly run automatically during and at the end of the simulation.  Some of the `Python` programs can or must be run stand-alone once the simulation is done.  The `Python` programs are shipped as part of this package, and are in `bin/python/`.  The top-level program is `bin/mc.js`, and most code it invokes is in `bin/js/`.

Despite the fact the directory is labelled `bin` these are source files.  The files with the `v4` prefix are generated from `master/v4.literate` (see the description of `.literate` files below).  For the rest, the master copy is in the `bin` directory.

There is a [ChangeLog](ChangeLog) you should keep up to date, but note it is for *user visible* changes in behavior.  Put internal changes in the [Log](#log) section of this file.

`package.json` describes this package--but note that doing a standard `npm install` is *not* recommended.

## File Extensions and Tools

### Node.js (.js)
Much of the system is in JavaScript, intended to be run under [Node.js](https://nodejs.org/).  We recommend the latest stable release.

`Node` has had many security problems; be careful where you install it, and keep current with updates.

### Python (.py)
The rest is written in [Python](https://www.python.org/).  Use `Python` 3, not the deprecated 2.

This package requires many additional packages in `Node` and `Python`; if you follow the installation instructions you will pick them up.

### Visual Studio Code
Lately we have been using [VSCode](https://code.visualstudio.com/) to do development, and since some of the code uses the `literate` extension (see below) it is close to a requirement to do development.  Here are all the relevant extensions we have added, along with their extension ids.  Most are optional, but make things easier:
  * Literate Programming (.literate files)
    * `literate` (jesterking.literate) literate programming. Essential if you work with the `v4` aka Heart Failure code.
    * `markdown AutoTOC` (wibblemonkey.markdown-auto-toc) this helps literate produce documentation
  * JavaScript (.js)
    * `jest`(Orta.vscode-jest) helps running our jest-based tests of `JavaScript`.
    * `Node extension pack` (Swellaby.node-pack) pulls in various extensions to help with `javascript` and `npm`.
    * `npm` (idered.npm) helps with the Node Package Manager.
    * `npm dependency` (howardzuo.vscode-npm-dependency) sidebar tool for `npm`
  * Python (.py)
    * `python` (ms-python.python)
    * `pylance` (ms-python.vscode-pylance)
    * `python debugger` (ms-python.debugpy)
  * Markdown (.md) Documentation
    * `markdown` (yzhang.markdown-all-in-one) help with documentation and notes
    * `markdown math` (koehlma.markdown-math)
    * `markdown pdf` (yzane.markdown-pdf) used to produce pdf versions of some of the docs

`VSCode` provides some level of support for most of these languages without extensions: `VSCode` is written (mostly?) in `TypeScript` which is a `JavaScript` variant, so there is a lot of support built in.  `VSCode` handles markdown natively, and some or all of the `Python` extensions may be built in.

### `.md` 
is for files such as this one that are in [markdown](https://commonmark.org/).  You may find this [cheat sheet](https://www.markdownguide.org/cheat-sheet/) helpful.  Markdown is intended to be readable and editable as plain text, but also convertible to other, richer formats such as `HTML` or `pdf`.  [Visual Studio Code](https://code.visualstudio.com/) has built-in markdown support that includes preview capabilities, and some extensions provide further support.

Note that markdown files typically preview nicely on github without further work.

### `.dia`
is for diagrams made with the free software diagramming tool [`Dia`](https://sourceforge.net/projects/dia-installer/). 

### `.svg`
is for "Scalable Vector Graphics", one of many standard formats for graphics. Vector graphics allow arbitrary enlargement while preserving resolution, which may be helpful with the somewhat cramped diagrams. These files are exported by `Dia` for inclusion in the User Guide.  markdown does not, AFAIK, directly support `.dia` files.

### `.literate`
are the master files for the literate programming extension to `VSCode`, [`literate`](https://github.com/jesterKing/literate).  [Literate programming](https://en.wikipedia.org/wiki/Literate_programming) is a general term for the creation of documents that are intended primarily for humans describing computer code.  The same source (`.literate` file in this case) can generate either documentation for humans or code for the computer.

`.literate` files are basically markdown, and for now you need to tell `VSCode` that they are markdown.  See [this](https://stackoverflow.com/a/51228725/4409451) for how to set that up.  This generates previews as you work (provided you issue a command in `VSCode` to show the preview), but to generate code files and `html` documentation you may need to run the `VSCode` command `literate: Process`--although the extension tries to do that automatically as you edit the source files.

As in other literate programming systems, chunks of code are identified by `<<name or description>>`; the `literate` extension refers to these as `fragments` and provides a fragment explorer to let you see and navigate among them.  If the description ends in `.*` (literally, e.g., `<<manage everything.*>>`) then it is a top-level fragment that can be assigned to an output file, listed after it on the same line.  So running `literate: Process` will produce all the output files named in such lines and an `.html` file with the same root name as the `.literate` file.  It does this for all `.literate` files in the same directory.

The `literate` extension is completely distinct from the `literate` system for literate programming; the former requires `VSCode` and should run wherever it does, while the latter does not need `VSCode`, should in principle run "anywhere", but has no readily available `MS-Windows` binaries and has its own required toolchain.

### Jest
This package uses  the [Jest](https://jestjs.io/) testing framework for `JavaScript`.  It looks under `__tests__` directories anywhere in the project for tests.  I have been using the `VSCode` `Orta.vscode-jest` extension to help run the tests, and set some options for it in `package.json`.

## Other Files

### `requirements.txt`
These are the package requirements for the `Python` code in the system.  The standard installation instructions tell the user to use this file during setup.

### `requirements-freeze.txt`
Captured the exact level of the packages at one point for a known working configuration. But time has passed, and you can probably ignore this.

### `bin/input_data.json`
one of the basic inputs to the monte-carlo simulation.  Automatically installed as needed.

### `data/`

Data files for use by the program.  Currently holds the codebook of variables for Heart Failure, which includes most standard variables as well.

### `doc/`
This directory includes user documentation and internal notes.  In general the `.md` and `.dia` files are the masters, to which edits should be made, while `.svg`, `.pdf` and `.html` files are derived from them.  Among the figures, `Process.dia` is mostly the master of the other 2 `Process*.dia` files (created by removing some elements in `Process.dia`), though I think I added a bit to `ProcessNew.dia`.   After conversion to `.svg` the figures appear in `UserGuide`.

As is typical, there is an issue about whether only the original sources or the derived files should go into version control.  The purist solution only puts the originals under version control.  The problem with that strategy is that it makes life harder for people, including users, who just want to see the final product.  In the case of `.literate` files it means even someone who wants to see the code would need to install `VSCode` and the `literate` plugin to get anything.  I have so far adopted a mixed approach, leaving `.pdf`'s out of version control and putting most other things in.  Building from the originals is particularly onerous because, as the next section reveals, there is not an automated build system.

### `master/`
This directory holds the `.literate` files that are the masters for some of the code--at the moment only `bin/js/v4*.js`.  They also include the human documentation generated from the `.literate` files as `.html`.  Note that even the "human" documentation is for developers rather than ordinary users.  Not that developers aren't human, dear reader!

## Build System
There isn't one, though maybe there should be.  The core of the application has been a bunch of `.js` and `.py` files that had no need to be built.  But things are getting more complex.  Typically, the developer will need to do these steps:
   1. Modify the code in its master place, either a `.literate`, `.py`, or `.js` file.
   2. Generate revised output from the literate files if any of them changed.  The `literate` extension should do this automatically.
   3. Test.  There is currently a small amount of automated tests, both for `Python` and `JavaScript`.  More would be good!
   4. Update `README.md`, `UserGuide.md`, and `Notes.md` if needed
   5. Generate additional documentation as desired.  At the moment, `UserGuide.pdf` comes from using the [`Markdown PDF`](https://marketplace.visualstudio.com/items?itemName=yzane.markdown-pdf) extension to generate it while viewing `UserGuide.md`.  I modified the default coloring because it made stuff in code format `like this` too hard to see.  One could also run html to pdf converters.
   6. Review `package.json` and `requirements.txt` to see they are still appropriate.
   7. Update `ChangeLog`.
   8. Bump version in `package.json`.
   9. Tag release.
   10. Push changes to github.
   11. Close or comment on any issues as appropriate.  Note that notations like `Fixes #11` in the commit logs will close issues automatically on upload.
   12. Tell the world.

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

See `Processing.dia` or its pdf export for a graphical representation of the data flow. The old Fortran model generated `outfile.dat` as its primary output, with summary measures for ~18 key variables.  These were accumulated in `MC/results/cumulative/{inp_file}_{NN}.dat` and then analysed by `sum_results.py`.  It also provided richer information on those variables, e.g., breakdowns by simulation year, and reports on many other variables in `{inp_file}_mc.out`.  Both these files and `outfile.dat` are formatted as tables for human consumption.  The `.dat` files are further processed by `format.py` which pulls selected categories (explicitly named in the code) to `{inp_file}_mc.frmt` (also human readable), saved as `{inp_file}_{NN}.frmt` for monte carlo runs.  While the individual files can be read by humans, there were no tools to summarize them, i.e., get mean and sd across simulations.  So we created `frmtToData.py` which dumps all the information into a computer friendly single-file database, customarily `allData.db`.  Then the GUI program `frmtReport.py` generates summaries for select variables.

# Heart Failure

The Heart Failure model adds a lot more states and variables to the model.  Rather than extend the previous outputs, which would require coding pretty-printing for the new variables, it simply dumps the variables into csv files, either `totresults.csv`, `targets_output.csv` (for target variables we want to calibrate the model to, but that are also relevant to the main analysis), or `calib.csv` (for results that are only of interest during calibration).  Each variable appears in only one of the 3 files, and many variables that are reported in `outfile.dat` or `{inp_file}_mc.out` are also reported in one of the .csv files.  The .csv files have 468 variables, including many that were not in the previous outputs, because they were not in the old model.  

As of 2023-06-30 here is a thought to be complete list of variables that do *not* appear in the csv files: *only* in `outfile.dat`: `DIS_DEINTERV$`, `DIS_DHINTERV$`, `DIS_DHCHD$`, `DIS_DHSTR$`, `DISC_NCVD$`, `DISC_TOT$`,  `DISC_LYRS`, `95PLUS_LYRS`, and `DISC_QALY`; *only* in `{inp_file}_mc.out`: `n95dh` and `totcost`.


Each line of the csv files gives results for a particular demographic group in a particular simulation year.  It uses the following codes:
agerange:
1=35-44,
2=45-54,
3=55-64,
4=65-74,
5=75-84,
6=85-94.

sex:
1=male,
2=female


# Other Notes

Command line from runSims.js usually has `-s` (save outputs), `-i` and `--seed` but no file names or directories.  Looking through the code, it seems `-s` only matters for outputs of the zero run.

I don't know where, but something seems to clear out `inp.txt` at the start of a run.  I ran after having done a preliminary run that produced `inp.txt` with headers and an initial line.  After the run started there was no sign of duplication.

`MC/inputs/input_data.json` read to find what to vary.  Use lists in 2 sections, 'dat_files' and 'inp_files'.  For 'dat_files' the zero run (`-z`) does nothing except write the data out.  For 'inp_files' the zero run writes out labels.  Both execute `vary()` on the file object and then `print_mc()`.

```python
  VFile(fname)
    pref,ext = fname.split('.')
    input: pref+'_mc0.'+ext
    output: pref+'_mc.'+ext
```

It reads from an `_mc0.EXT` file and writes to `_mc.EXT`.

`DatFile` includes an `SDFile` but `InpFile` includes `Effects`.
  *  `DatFile(file_data, random_generator)` where `file_data` is a `JSON` structure
    that includes 'filename' -> `modfile/FILENAME.dat` as primary input (for `VFILE`).

`InpFile(fname)` calls `VCFile(fname+'.inp')` and then creates
  *  `Effects` which has no arguments.

`Effects` reads from `MC/inputs/inp_distribution.txt`.
  *  Writes to `MC\input_variation\inp.txt`.
  *  Uses `Component` in a transitory way to wrap some lines.
  *  This javascript code in `runSims.js` actually fills in the iteration number which is the first field on the data lines:

   ```javascript
        let str = String(i + ' '.repeat(16));
        let INP_OUTPUT_FILE = './MC/input_variation/inp.txt';
        if (fs.existsSync(INP_OUTPUT_FILE)) {
            fs.appendFileSync(INP_OUTPUT_FILE, str.substring(0,16) + '  ')
   ```

`Component` actually generates the random number and interprets 
    parameters.  It would probably be better to generate them once and retain them.
    Although `Component` instances are temporary, there is persistent state held in the class variable [check it's not actually in some other class].  This is the state of the random number generator for each group.

Note that `montecarlo.py` is only used to generate a single simulation.  Because of the state-keeping in `Component` it would actually generate the same numbers if called again.

An effect may be made of several components that are summed or added to the mean.

2022-09-13 Start `issue12` branch to fix random number generation with LogNormal .inp files.
Initial focus on being able to run tests.  Create `py_tests` folder at very top level to use the pytest framework, and configure `VSCode` for same. Created `test_monte.py` and, after painful experiments with getting it to load the code, made a simple test work.

Further testing of `Effects` revealed 2 different ways the code was inconsistent with the current `numpy.random` interface:
  1. The state has moved to the `BitGenerator` and is not directly accessible.
  2. `randn` is obsolescent (it is still available, but not through the old interface).
Fixed both.

# Sampling for .inp and .dat Files

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

# Getting Error Info from Python

When `montecarlo.py`, invoked from `runSims.js`, fails, very little information gets back, just a message "montecarlo.py run failed".  This is unhelpful.  Neither the exact call used to invoke the python program nor the traceback for the error or console output (if any) is available.

Some of this stems from the use of `{silent:true}` option, which is the default, for the invocation of `shelljs` (which is the module name, even though aliased to `shell`).  Apparently the return value for a syncronous call is a `ShellString`.  See https://github.com/RossBoylan/mccli/issues/20#issue-1443014991 for more.

The `python-shell` module advertises much better error reporting, but I've never been able to get it to do anything.  My latest attempts apparently couldn't even get it to run anything.  I have *2* different branches experimenting with the package, *both* named `python-shell`.  The primary archive in `J:\source\repos\mccli` has that branch with work from Feb 2022.  The archive in `C:\Users\rdboylan\Documents\KBD\mccli-release`, intended for production runs, has some *different* work from Nov 2022.  It is not based on the earlier branch.

# Log

2023-11-27
----------
Created a `doc/` subdirectory and moved much of the recently created documentation to it.

Added general instructions for contributors and a table of contents to `Notes.md`.

Created `master/` subdirectory to hold `.literate` files, part of the introduction of literate programming tools into the system as discussed in `Notes.md`, `literate.md`, and `v4.literate`.  The requires `VSCode` and its `literate` extension for the full development cycle.   See `literate.md` for the pros and cons of various alternatives.

2022-09-14
----------
Modified test code to write out iteration number.

# To Do

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
  - [ ] Update to handle Heart Failure model (Sue)
    - [ ] if possible keep single code base
    - [ ] identify differences between current production version on c: and interruptible version on j:
    - [ ] add new dat files. done on j: input.json, HF branch
    - [ ] create program to gather new output files and put results in db
      - [x] note we have less information about labels, and may not have the category info expected.  However, we now have a full codebook with long variable descriptions.
      - [x] possibly make this selective: only some variables
          ```
          The variables that I need for the hypertension cascade paper will be:

          From Targets_output.csv
          •	pnchd
          •	astrokde
          •	ahstrokde
          •	hfinc
          From totresults.csv
          •	ntreatde, 
          •	nchdi, 
          •	nchditot,
          •	intstrok,
          •	inthstrok, 
          •	inthfinc
          ```
      - [ ] make it a long running process across simulations
    - [ ] maybe create command line program to extract results from db
    - [ ] maybe add option to skip generating the format files
    - [x] set up testing system for javascript
      - [x] selected jest
      - [x] install it for current project
      - [x] install associated VSCode extension.  The one the jest site points to is the most downloaded, but not the highest rated. I go with it; many of the alternatives do not target my use.
    - [x] write at least one real test case.
    - [ ] may need to modify design to make it more easily testable
    - [x] implement/test reading the codebook
    - [ ] learn about async code + database
      - [x] what guarantees does the sqlite3 make about async and multithreaded behavior?
        - [x] the javascript library `better-sqlite3`
            *  According to docs "Transaction functions do not work with async functions" and
              "because SQLite3 serializes all transactions, it's generally a very bad idea to keep a transaction open across event loop ticks anyways."
            * Surrounding discussion suggests the meaning is that the function passed to `Database.transaction()` must be synchronous, i.e., must be all done when it exits.
            *  The library is synchronous, i.e., the javascript functions it exposes are synchronous.
            *  Multiple worker threads each open the db and manipulate it.
        - [x] the underlying sqlite engine
            * multiple processes can open the same database at once
            * only one can modify the database at a time.  This is enforced with locks, which are not totally reliable on some systems (e.g., NFS).  Multiple processes can write to db, but they will be serialized by the lock.
            * is threadsafe (if compiled with appropriate options, which it is in MS-Windows binaries), but threads are discouraged
            * I find no explicit documentation about opening multiple connections from the same process, but presumably the thread safety means this will work too.
      - [ ] learn about async operations generally in `javascript` and `node.js`
        - [x] can I put synchronous calls inside an async function? Yes.
        - [x] can I use more than one thread? Information seems contradictory, depending partly on the definition of "use".
          + In the OS sense of  thread, No, except that some tasks in C++ (called from certain `javascript` functions) run on additional  threads in the "Worker Pool".  From the standpoint of the `javascript` code I write, which is all in the main thread aka "Event Loop", there is only one thread.  But the code will execute in async fashion.
          +  `Node.js` website: "JavaScript execution in Node.js is single threaded". But it also says "Node.js uses a small number of threads to handle many clients. In Node.js there are two types of threads: one Event Loop (aka the main loop, main thread ...), and a pool of k Workers in a Worker Pool (aka the threadpool)."  Worker threads are for `libuv` and handle I/O and CPU intensive tasks like compression and crypto.
          +  But it appears [getting a task on a worker](https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Asynchronous/Introducing_workers) can be done fairly easily, without using `C++`.  Technically that gets a function on a `Worker`, but the same source says this uses different threads.
        - [ ] multiple "threads" (including async processes on the same thread) and Promises
          *  https://stackoverflow.com/questions/18217640/what-happens-if-i-reject-resolve-multiple-times-in-kriskowals-q/18218542#18218542 offers somewhat contradictory info on what happens if multiple threads try to resolve the same Promise.  It seems it is resolved only once, but later callers can still retrieve the value.
          *  See also https://stackoverflow.com/questions/20328073/is-it-safe-to-resolve-a-promise-multiple-times?rq=3.
          *  https://262.ecma-international.org/6.0/#sec-promise.resolve is authoritative, but cryptic.
        - [x] `await` can only be used in an `async` function or at module level.
        - [x] callback API has better performance (memory, time) than Promise-based API, at least for `fs` module.
        - [x] `await` can be viewed as an easier way to sequence operations than `.then()` chaining Promises, which in turn are easier then the callback approach. 
    - [x] initial database setup
      - [x] name of output db.  Allow run-time selection. `hfmc_results` might be a good default,  Or embed time stamp in it.  Or use name in existing python code, `MC\results\breakdown\allData.db`
      - [x] directory of output db: `MC\results\`
      - [x] embed in transaction
      - [x] fix: current code will try to make a database transaction the first time--before there is a database!
            Literally, `master.db` will not exist.  Likely solution:
            - [x] make database creation part of master
            - [x] that will mean we might create the database when there is no output
            - [x] move the done code to Master as well (from `SimDataSource`)
      - [x] remove the nested transactions, and the accompanying comments
    - [ ] check location of codebook info.  It seems it goes in `SimDataSource.#byvar`, but it's only read once for all `.csv`'s.
    - [ ] implement the long running code that reads `csv`'s.  Even apart from the database setup, the code is a work in progress.
      - [x] embed in transaction
    - [x] create top-level flow that waits for iteration to complete and launches processing of all `SimDataSources`
    - [x] remember there may be a scenario, with multiple scenarios per run
    - [ ] `Jest` scans directories I tell it to ignore and takes > 1 minute
      - [ ] See my [question](https://stackoverflow.com/questions/77951697/how-to-stop-jest-from-scanning-directories) asked 2/6/24
      - [ ] Temporary solution: move `[Mm]od92_*` directories to `mccli-models`.
    - [ ] integrate into the main program
    - [ ] verify that the user documentation matches actual behavior
    - [ ] test performance
