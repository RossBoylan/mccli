Notes on what files montecarlo.py uses.
This is to aid testing.

Command line from runSims.js usually has `-s` (save outputs), `-i` and `--seed` but no file names or directories.

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
`Component` actually generates the random number and interprets 
    parameters.  It would probably be better to generate them once and retain them.
    Although `Component` instances are temporary, there is persistent state held in a class variables.  This is the state of the random number generator for each group.

Note that montecarlo.py is only used to generate a single simulation.  Because of the state-keeping in `Component` it would actually generate the same numbers if called again.

An effect may be made of several components that are summed or added to the mean.

2022-09-13 Start issue12 branch to fix random number generation with LogNormal .inp files.
Initial focus on being able to run tests.  Create `py_tests` folder at very top level to use the pytest framework, and configure `VSCode` for same. Created `test_monte.py` and, after painful experiments with getting it to load the code, made a simple test work.