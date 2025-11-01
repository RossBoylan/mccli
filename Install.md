# How to Setup `mccli`

The first part of this document describes the recommended steps for getting `mccli` working on a new computer.  As the `Fortran` model file it uses is only available for `MS-Windows`, the instructions are geared to `Windows`, though they do use `/` rather than `\` as a directory separator.

The second more-than-half is non-essential [commentary](#commentary).  It discusses why the instructions say to do some things, alternatives that may be appropriate for some, and things that might go wrong and what to do about them.

There are many choices one could make along the way.  If you already have something installed that meets the need, you can skip the relevant step or customize it as you prefer.

Although I said the basic instructions would avoid choices, there are a couple that you need to make at the start.  We begin with those.

## What Do You Want to Do?
If you want to [collect custom statistics](bin/python/frmtReport.py) after doing the simulation you should install `Python` 3.10 or earlier, and uncomment `PySide2` in `requirements.txt`.

If you want to develop `mccli` itself, including debugging failures, uncomment the developer tools in `requirements.txt`.

I'll mention these again at the appropriate place.

Avoid installing things from the Microsoft Store to avoid reported quirks.

## `Git`
Install `Git`, e.g., https://gitforwindows.org/.

## Get `mccli`
Change to your `Documents` directory and open a terminal.

`git clone https://github.com/RossBoylan/mccli.git`

The code will then be in `Documents/mccli`.  Change to that directory in the terminal:

`cd mccli`

## Tweaks

The project has various "branches" with different code in each.  The default may not be appropriate for your analysis.  Change to your desired branch, e.g., for branch `justice` do

`git checkout justice`

Then, if you want to get the custom statistics referred to in the [first section](#what-do-you-want-to-do), open `requirements.txt` in any text editor, find "pySide2" in it (near the bottom) and remove the `#` at the start of the line.

Similarly, if you want to develop/debug the software, remove the leading `#` from all the developer software at the bottom under `##### Developer modules ##########`.  Currently that's `debugpy`, `pytest` and `pytest-cov`.

Then save the modifications over the original file.

There's more work before it's ready to run.

## `Node`

Install [Node](https://nodejs.org/); we recommend the LTS version.  If you have already installed it, check that it is up to date; `Node` notoriously suffers security bugs.  `node --version` gives the version installed.

Then, in the terminal you already have opened, type

   `npm install colors fs fs-extra inquirer path progress shelljs single-line-log yargs`

Do *not* execute `npm install` with no arguments and do *not* use the `-g` option.

## `Python`

Install [python](https://www.python.org/downloads/).  Get the latest supported version unless you need the custom reports from `frmtReport.py`, which requires `Python` 3.10 or earlier on `MS-Windows`.  We recommend a system-wide installation, which requires administrative rights, and adding `python` to your `PATH`.

Note that multiple versions of `Python` can be installed at once.

Create a [Python virtual environment](https://docs.python.org/3/library/venv.html).  Virtual environments allow you to control which version of `Python` and which version of packages a project uses.

From the `mccli` root (you should already be there) create a virtual environment with
```shell
py -m venv pyenv   # Windows
py -3.10 -m venv pyenv  # Windows with an old version of Python
python3 -m venv pyenv  # most others
python -m venv pyenv   # some others--do `python --version` first to check it is python3
```

Once you create the environment you must activate it.  When the environment is active the prompt will change, with the environment name appearing first, e.g., `(pyenv)`, and you will get the version of python specific to that environment when you type `python` (using `py` on Windows is not as reliable a way to detect the virtual environment).  When you install packages, as we are about to do, they go in the environment and are only visible from there.

The exact command to activate the environment varies with the operating system and choice of shell (a table toward the end of the [Creating virtual environments](https://docs.python.org/3/library/venv.html#creating-virtual-environments) section has them all).  Assuming you are in the `mccli` root directory, the 3 most common choices
```shell
pyenv\Scripts\activate.bat   # Windows command prompt
pyenv\Scripts\Activate.ps1   # Windows powershell
# remember the source command below
source pyenv/bin/activate    # *nix bash/zsh
```
Type whichever is appropriate.

Now install the `Python` packages that `mccli` requires.  These are documented in `requirements.txt` in the root folder of `mccli`.   Assuming you have made any necessary [tweaks](#tweaks) to it, 
```shell
python -m pip install -r requirements.txt  # or
python -m pip install -r requirements.txt  --user   # if you are not in a virtual environment
```
should install all necessary packages.

## `Fortran`

The core model is written in `Fortran` and distributed as a binary program, typically `CVDMODYY.exe` where `YY` is a year.  We distribute that as part of the specific project, not with the `mccli` code.  Recent versions have been built with Intel compilers, and require the installation of supporting libraries to run.

Get the installer (it may be with the CVDMOD file), e.g., `w_ifort_runtime_p_2024.2.0.980.exe` and run it to install the necessary libraries.

## Commentary

This section includes motivations for some of the steps and more in-depth information that is not necessary for following the installation steps.  It is grouped by the sections above.

### Git

If you really don't want to use `git`, you can go to the website, and
  1. select the `Code` tab
  2. choose your desired branch
  3. click the green `Code` button
  4. choose `Download ZIP`.

![alt text](tar_from_github.png)

On the other hand, if you like `git` but want something that gives you more choices for using it from `Windows Explorer` via right-click, consider adding [TortoiseGit](https://tortoisegit.org/download/).  It assumes `Git for Windows` is already installed.

There are many graphical and command line tools available for `git`.  Our recommended development tool, [Visual Studio Code](https://code.visualstudio.com/) has extensive `git` and `github` support.  It also assume you already have `Git for Windows` installed, which is why we recommend that particular flavor for `MS-Windows`.

There are some tools distributed by `github` that are specificaly geared to github.

For a simple gui, execute `git gui`.

`git` recognizes what repository it is in based on the current directory; you generally should be inside the project before running a `git` command.

### mccli

There is absolutely nothing magical about `Documents/mccli`; you can pick any location you like.  You can even pick any project name you like, e.g., 

`git clone https://github.com/RossBoylan/mccli.git mccli-justice`

will create the project in the `mccli-justice` directory.  You probably then should ensure that is on the `justice` branch.

See [ChangeLog](ChangeLog.md) for details about how the software has changed for users, and [Notes for programmers](bin/python/Notes.md) for developer-oriented material.

### Tweaks

Changes to `requirements.txt` only take effect when you execute

`python -m pip install -r requirements.txt`.

If you change your mind later you can install, remove, or update packages using `python -m pip` commands from inside the virtual environment.  We recommend keeping `requirements.txt` up to date with your package selection as well.

The one thing you can't easily do is change the version of `Python` a virtual environment uses.  That is why we emphasize deciding up front if you want the specialized reports that `frmtReport.py` provides, because it requires `pySide2` which requires `Python` 3.10 on `MS-Windows`.  There literally aren't any versions of `pySide2` available as binaries for later versions.

### Node

*Danger!* Simply using `npm install` will also install the packages. But it also updates the system, including the shortcuts `mc` to invoke the program, and possibly some libraries:
   * If you have the old version installed running `npm install` with the new version will likely trash the old installation.
   * The shorcuts established by the installation are almost certainly ignorant of the python virtual environment which we recommend creating below.

*Do not use the `-g` option to `npm`*, since the package, as part of the general behavior of `Node`, does not load packages from the global environment (!).

`npm install ....` will create a `node_modules` directory; it is very similar in intent to the `pyenv` directory: it holds a project-specific library of packages.

### Python and its Virtual Environments

If you install an older version of `Python` you probably don't want to tell the installer to add it to the `PATH`.

Note that the `py` command is specific to `MS-Windows`.

You do not have to use a [Python virtual environment](https://docs.python.org/3/library/venv.html), although some of the test code may assume you do, and even that it is in the `pyenv` directory.  A virtual environment does require a little more setup, but it separates this project more cleanly from others.  In particular, it reduces the chances you will break unrelated programs.  So that's what we describe here; you can skip the virtual environment steps if you're feeling lucky.  So there's one question you've got to ask yourself: "Do I feel lucky?" Well, do ya, punk?

The careful reader will have noticed the word *reduces* in "reduces the chances you will break unrelated programs".  It did not say it *eliminates* the risk.  If you install a python module, like `pySide2`, that depends on non-python libraries like `Qt`, they may still end up being installed system-wide and cause trouble.

Virtual environments also allow you to pick which `Python` version to use so that you can, for example, have a virtual environment running `Python 3.10` and using the `pySide2` module while your main system, and other projects, use the current release of `Python`.

Each time you login, in fact each time you start a new terminal, you will need to activate the virtual environment.  No matter how you started, `deactivate` will disable the environment.

If now or later, specifically when running `frmtReport.py`, you get errors related to the graphics system, one possible cause is that you need to install the `Qt` libraries (written in C++, not Python).  You can get them through the green [Download the Qt Online Installer](https://www.qt.io/download-open-source) button at the bottom of the page.  Be aware that `pySide2` works with `Qt5`, which is no longer current.

### Fortran

Older versions of the model did not use the Intel compiler. I think they used Leahy. Both the compiler and the libraries it distributes have various versions.  We believe, and have some experience which is consistent, that matching the version of the compiler and the version of the library is not essential.  Using something built with an earlier compiler with later libraries is most likely safe.  And we have run executables from later compiler with an earlier library, apparently successfully.  There may be some performance penalty if using an earlier library.

`Fortran` library installation only needs to be done once, and ordinarily applies to the whole system.  So we recommend using the most recent version available.

Note that the installers, such as `w_ifort_runtime_p_2024.2.0.980.exe`, do not need to be present for the model to run.  The libraries that they install do need to be present.
