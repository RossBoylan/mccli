Maestro
=======

Purpose
=======

`maestro`'s purpose is to get results of simulations faster, and with less human work, than would be possible using `mc run` alone.  It does so by running simulations in parallel.

`maestro` is the conductor of all the individual simulations; its modules (`Python` code) are in the `symphony` directory.

Most results are available directly under the main project directory and full results are under the `parallel` directory.  The parallelization is by `.inp` file; simulations for each `.inp` run separately and simultaneously. 

`maestro` currently uses a command-line interface only.

The monte-carlo system and the `Fortran` model it runs are not designed for multiple parallel runs.  Simultaneous runs in the same directory may step on each other, producing either obvious crashes or more subtle corruption.  To avoid such difficulties, `maestro` makes multiple copies of the project directory; each run is in a separate directory.

`maestro` is a stopgap solution because the ideal solution, changing `mccli` and the programs it invokes, especially the `Fortran` model, to run safely in parallel in a  single directory, seems riskier and more time-consuming.

Instructions
============

  1. Install `mccli` as described in the general [README](../../README.md), if you haven't already.
  2. Create a project directory, separate from the code, and set up the project for analysis as usual.  Try to avoid extraneous files, as they are likely to be copied many times.
  3. If you are using  a `Python` virtual environment (you are if you followed the standard `mccli` instructions), activate it.
  4. Execute subsequent steps from a terminal in the top of the project directory.  Running from the `mccli` directory will not work.
  5. Run `mc init` as usual, selecting *all* scenarios (`.inp` files) you wish to consider.  Then do any post-init setup necessary to get the project ready for a usual `mc run`.
  6. Review the [Requirements](#requirements) below.
  7. Check the code for `maestro.py` in light of the [Cautions](#cautions) below, and make any changes necessary.
  8. Run `python maestro.py`.  The `python` is there to ensure you get the version associated with your virtual environment.
  9. When it finishes, if you don't want any of the extra information, delete the `parallel` directory and all its children.  This will retain the `MC_xxx` directories under the main project with the `MC` results.  Ordinarily, most of the space occupied will be there.



Cautions
========

This is alpha-quality code, currently in development.  You should review the decisions in the code for appropriateness for your purposes and system:

  1. Are the directory choices appropriate for your project?
  2. Are the options used to invoke the monte-carlo simulation, in particular the number of simulations, the seed, and the use of `--overwrite` appropriate?
  3. Does the active code either copy the files with `prepare()` on first invocation or use `prepare_basics()` if the working directories are already set?
  4. Does it use the [message handlers/loggers](#message-handlers) that you want?
  5. Does it setup and invoke the runs?


You may think that many more of the files and directories copied could be symbolic links as well, thereby saving space and time.  `mccli` and the software it calls *write* to most directories, even ones with "input" in the name.  It writes to many "input" files. So if you get the urge to convert copies to links, resist it.

`maestro.py` depends upon `mc run` being invoked with `--json`; do not remove that option.

Message Handlers
================

`maestro` processes terminal output from the individual runs as `JSON` messages.  It can use any combination of the following (from `symphony/message_handlers.py`):

  * `StupidLogFile(aPath)` will dump all messages as text representation of `JSON` to the file at location `aPath`, which may be a string or a `pathlib.Path` object.
  * `DumbTerminalLog()` prints the messages as text for `JSON` to the terminal.  This can be used in a dumb terminal because it makes no attempt to colorize, ring bells, or address different locations on the screen.
  * `TerminalTimerLog(niter, nrun, updateInterval=timedelta(minutes=5))` also requires only a dumb terminal, but is much more selective and intelligent in its output.  It records timing information for each of `niter` iterations of
  the model across `nrun` parallel runs.  Every `updateInterval` it prints a summary progress report, including estimated time of completion for the entire batch, as well as the individual runs.  These estimates are based on the average time across all iterations, and so will differ from those of `mc run`, which uses the time of the most recent iteration only to estimate time remaining.

Requirements
============

Your system must have adequate RAM, disk space, and CPUs to handle the parallel runs.  In testing, each run required 1.6GB of RAM.

This was developed for `MS-Windows` and might have issues on other platforms.  Further, because it creates symbolic links, it requires somewhat recent versions of `Windows` or admin rights.  The current implementation uses symbolic links, not the older junction points (I think: exact behavior depends on `Python`'s `pathlib.Path.symlink_to()` implementation).  Symbolic links work on all `Unix` variants, including `Linux` and `MacOS`.

Operation
=========

`maestro` creates a `parallel` subdirectory of the main project.  For each **run**, a single execution of `mc run`, it creates a directory under `parallel`  and copies the project files to that subdirectory.  There is one run for each scenario (`.inp` file), in a directory named after the name of the `.inp` file without the extension.  Each is set to simulate only one of the `.inp` files, even though in `mc init` you specified a simulation that would ordinarily run all, serially, within the same simulation.

There will be `MC` directories under the subprojects; these are actually links to directories named `MC_xxx` under the main project.  This means that when the runs finish one can simply look to those directories for the results.

So the original setup looks like this (simplified):
```
myproject
myproject/MC
```

Supposing  there were 2 scenarios, a and b, after setup it would be
```
myproject
myproject/MC
myproject/MC_a
myproject/MC_b
myproject/parallel
myproject/parallel/a
myproject/parallel/a/MC (links to myproject/MC_a)
myproject/parallel/b
myproject/parallel/b/MC (links to myproject/MC_b)
```

with all relevant files and directories from `myproject/` copied to the `a` and `b` directories, modified as necessary.

`maestro` then launches `mc run` in each subproject `parallel/xxx/`, monitors the progress, and reports the results.  The exact behavior depends on the [message handlers](#message-handlers) (`symphony/message_handlers.py`) installed in the `Switchboard` of the main program.

With standard code (from `symphony.message_handlers.StupidLogFile`), `parallel/runlog.txt` will have all the messages generated by all the runs.  If you are not also dumping those messages to the terminal (`symphony.message_handlers.DumbTerminalLog`) you can monitor the file as the program runs to see progress.  Because of caching, messages may not be visible instantly.  All messages are in `JSON` format.

Variation
=========

As noted earlier, if `prepare()` has already set up the copies, just call `prepare_basic()` to avoid recopying, which might or might not produce errors or toss results of previous runs.

`prepare(basics, stemcell="/some/path")` will make a single copy of the project directory to `/some/path`; it will not create the `parallel` directory or anything under it, and it will  not modify the request to simulate multiple `.inp` files.  This exists mostly as a convenience for testing; one can then do a reqular run of `maestro` from the newly created copy.

Future
======

Perhaps one day there will be a GUI, or at least output that treats the terminal as a 2 dimensional surface, `curses` style (`Python curses` is not available on `MS-Windows` and an implementation for `Windows` seems unmaintained and not working).

The logs could go to a database instead of a file.

A richer range of statistics and estimates for the runs might be helpful.

Each run does all iterations for a single scenario/`.inp` file.  `maestro` could allow several input files in a single run, for example to limit the number of parallel runs.  Or, the runs could be further broken down so that each does only a portion of the iterations to be covered.