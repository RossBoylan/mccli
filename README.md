# Montecarlo CLI (Command Line Interface)

WARNING: versions 3.4+ are for use only with the new Heart Failure Fortran model.

WARNING: v 3.0 changes the meaning of inputs for the lognormal, beta and gamma
distributions.  The inputs now are the mean and standard deviation of the generated
variables for *all* distributions.  For distributions related to interventions (`.inp` files) this wasn't the case until v 3.3.

Only certain parameter values are legal, as was true before, e.g., standard deviations can not be negative.  Usually the restrictions are obvious: the mean must be in the domain of the corresponding distribution, i.e., $>0$ for lognormal and gamma, in $(0, 1)$ for beta.  The most subtle one is that $s$, the standard deviation of the beta, must satisfy $s^2 < m (1-m)$, with $m$ the mean.

Previously, the input parameters were the "native" parameters of the distribution (not always a well-defined concept; operationally the parameters `NumPy` uses), which means that to use those old inputs with the new code you must translate them into the implied mean and standard deviation.  

As an example of translating from the old to new parameterization, consider the lognormal.  Recall that $Y$ has a lognormal distribution if $X = \log(Y)$ has a normal distribution.
The old interpretation was that the mean and sd referred to $X$; under the new scheme they
refer to $Y$. If $a$ and $b$ are the mean and sd of the normal ($X$), and $m$ and $s$ are the mean and sd
of the log-normal, they are related by

$m = \exp(a+b^2/2)$

$s^2 = (\exp(b^2)-1)\exp(2a+b^2)$.

So, if you're being mechanical, the old $a$ and $b$ must be changed to the new $m$ and $s$.
However, that exercise might reveal that the old values weren't sensible, in which 
case a rethink would be in order.

There are other more subtle changes to the handling of correlated random numbers.  The old code was
ineffective in inducing correlations for beta, and possibly log-normal, distributions.  The new
code should generally induce higher correlations, though they will necessarily be imperfect.  The correlations for interventions continue to be handled the old way, for now.

The previous discussion was a slight simplification: the program actually will accept "impossible" inputs in some cases and reinterpret them as described below.

## Usage
```
Usage: mc <command> [options]

Commands:
  init                   initialize Montecarlo files

  run-sims [iterations] [start] [seed]      run MC simulations
                                                       [aliases: run, r]

Options:
  --python, --py     python interpreter to use   [string] [default: py probably only works on MS-Windows]
  --help          Show help  


Use mc run --help for fuller meaning of arguments


Usage: frmtToData.py
Scans the output of a simulation run and converts it to a single datafile.

Usage: frmtReport.py
This GUI takes the datafile produced by frmtToData and shows a list of variables.
If you click on a variable the program will output a summary file.
The purpose here is to produce summaries for variables that the basic monte-carlo runs do not summarize.
```

## Getting Started

### TESTING!
This code is under development, may not work properly, and might seize your firstborn.

### Get Source

This code is the `justice` branch of RossBoylan/mccli on github.com.  Despite that, it is still identified as "@ecfairle/mccli",
and because of that the conventional installation with `npm install` may not work, especially if you have already installed the earlier version.

I recommend putting a copy of this package on your local hard drive, e.g., `Documents\mccli`.  You can clone it from github and switch to the `justice` branch,
or get it from an archive file.

The [ChangeLog](ChangeLog.md) provides the history and features of this code

### Node Setup

If you have not done so, install [Node](https://nodejs.org/); we recommend the LTS version.  If you have already installed it, check that it is up to date; `Node` notoriously suffers security bugs.  `node --version` gives the version installed.

To ensure setup, you should change to the top directory for `mccli`, e.g. `Documents\mccli\`, if you are not already there, and use a terminal (e.g., type command prompt in MS Windows) to execute

   `npm install colors fs fs-extra inquirer path progress shelljs single-line-log yargs` 

*Danger!* Simply using `npm install` will also install the packages. But it also updates the system, including the shortcuts `mc` to invoke the program, and possibly some libraries:
   * If you have the old version installed running `npm install` with the new version will likely trash the old installation.
   * The shorcuts established by the installation are almost certainly ignorant of the python virtual environment which we recommend creating below.

*Do not use the `-g` option to npm,* since the package, as part of the general behavior of `Node`, does not load packages from the global environment (!).

### Python Setup
If you don't already have Python3 on your system, install [python](https://www.python.org/downloads/).  If you install it system-wide, which requires administrative rights, and add python to your PATH, life will be easier later.

**WARNING** Which version of `Python` to install depends on a decision you will make later about whether to use the `pySide2` module.  We mention it here because the last version of `Python` on `MS-Windows` with available binaries for `pySide2` is 3.10.  So download that if you intend to keep `pySide2`.  We recommend first-time users comment out `pySide2` and get the latest stable `Python`.  See the comments in the `requirements.txt` file for more details.  

Although using a [Python virtual environment](https://docs.python.org/3/library/venv.html) takes a little more setup, it separates this project more cleanly from others.  In particular, it reduces the chances you will break unrelated programs.  So that's what we describe here; you can skip the virtual environment steps if you're feeling lucky.  So there's one question you've got to ask yourself: "Do I feel lucky?" Well, do ya, punk?

The careful reader will have noticed the word *reduces* in "reduces the chances you will break unrelated programs".  It did not say it *eliminates* the risk.  If you install a python module, like `pySide2`, that depends on non-python libraries like `Qt`, they may still end up being installed system-wide and cause trouble.

Virtual environments also allow you to pick which `Python` version to use so that you can, for example, have a virtual environment running `Python 3.10` and using the `pySide2` module while your main system, and other projects, use the current release of `Python`.

From the `mccli` root (you should already be there) create a virtual environment with
```shell
py -m venv pyenv   # Windows
python3 -m venv pyenv  # most others
python -m venv pyenv   # some others--do python --version first to check it is python3
```
Note that the environment does not need to be called `pyenv` and it can be anywhere you like.  `pyenv` is already in `.gitignore`.

Once you create the environment you must activate it.  When the environment is active the prompt will change, with the environment name appearing first, e.g., `(pyenv)`, and you will get the version of python specific to that environment when you type `python` (using `py` on Windows is not as reliable a way to detect the virtual environment).  When you install packages, as we are about to do, they go in the environment and are only visible from there.

The exact command to activate the environment varies with the operating system and choice of shell (a table toward the end of the [Creating virtual environments](https://docs.python.org/3/library/venv.html#creating-virtual-environments) section has them all).  Assuming you are in the `mccli` root directory, the 3 most common choices
```shell
pyenv\Scripts\activate.bat   # Windows command prompt
pyenv\Scripts\Activate.ps1   # Windows powershell
# remember the source command below
source pyenv/bin/activate    # *nix bash/zsh
```

You are more likely to be in a directory holding your analysis later, in which case you will need a more elaborate path to refer to `pyenv`.

Each time you login, in fact each time you start a new terminal, you will need to activate the environment.  No matter how you started, `deactivate` will disable the environment.

Now install the `Python` packages that mccli requires.  These are documented in `requirements.txt` in the root folder of `mccli`.   You may want to skip some of the packages listed in `requirements.txt`, in particular the heavy graphics of `pySide2` are only needed for some post-analysis.  You can review the comments in `requirements.txt` and comment out or delete any packages you don't want. Save the file.  Then 
```shell
python -m pip install -r requirements.txt  # or
python -m pip install -r requirements.txt  --user   # if you are not in a virtual environment
```
should install all necessary packages.

If now or later, specifically when running `frmtReport.py`, you get errors related to the graphics system, one possible cause is that you need to install the `Qt` libraries (written in C++, not Python).  You can get them through the green [Download the Qt Online Installer](https://www.qt.io/download-open-source) button at the bottom of the page.

Later on you can keep your packages up to date with
```shell
python -m pip list --outdated  # shows which packages are old
python -m pip install --upgrade -r requirements.txt # actually upgrades the packages
python -m pip install --upgrade randomgen numpy   # like this to upgrade specific packages
```


### Node Virtual Environment

`Node` has something very like the Python virtual environments.  Just as the `pyenv` directory created above holds a bunch of Python packages and related materials that are specific to this particular project, the `node_modules` directory holds the complete set of node modules used for this project.  Both directories are in the project's `.gitignore`, so you don't get overwhelmed by huge lists of files when you are working with `git` (version control system).

### First run

Then, assuming you have activated the Python virtual environment, this package is in `Documents\mccli`, the model files are in `Documents\mymodel`, and you are in the latter directory, type
`node ..\mccli\bin\mc init`
to set it up.  There are actually a lot of supporting files required to specify the model, discussed later.

Once that's done, 
```shell
node ..\mccli\bin\mc run <nsims> <first index> <seed> --python ..\mccli\pyenv\Scripts\python.exe  # Windows
node ../mccli/bin/mc run <nsims> <first index> <seed> --python ../mccli/pyenv/bin/python   # *nix
node ..\mccli\bin\mc run 5 0 8093218 --python ..\mccli\pyenv\Scripts\python.exe # e.g., to run 5 simulations starting at 0.  Index 0 is special because it uses the original parameters.
```

`node ..\mccli\bin\mc --help` for more information, and
`node ..\mccli\bin\mc run --help` for even more information on the `run` command.

If you're curious, the reason for using `node <path to main file>` instead of just `mc` is that `mc` only works when it was registered as a global
shortcut by `npm install`, which these instructions deliberately avoid using.  To be sure of getting the right version we invoke `node` directly and give it the location of the file
to execute.

### Later Runs

If you want to execute a variation of the original simulation, rename the `MC` folder to something indicating what it contains and rerun `mc init`. If you are varying the risk factor intervention input you will then need to create  `MC\inputs\inp_distribution.txt`, described below.

If your first run is part of the total run, e.g., repetitions 0-499, and you want to run the remainder, 500-1000, it may not automatically combine results. Instead at the start of the run the program will ask `do you want to save these results (otherwise they will be written over)`.  We should  probably fix that.

On Windows things might work ok without the `--python` argument; if it is not specified the default `py` is used to invoke python. `py` will probably be able to launch python, but the one it launches may not be using the virtual environment.  The simpler form `--python python` has a better chance of picking up the virtual environment.  For `*nix` systems the default `py` to invoke python will not work; again using python or python3 without a path might work, and explicitly specifying it, as shown above, is safest of all.

### A Shortcut
Because it is often convenient to define some shortcuts to refer to the possibly cumbersome paths to the `mc` program, the `python` embedded in the proper virtual environment, and other programs like `maestro` that you may want to run, it can be convenient to write a script that takes care of all these steps, as well as activating the `python` virtual environment.

[my](my.ps1) is a script I use for `Powershell`.  As noted in its comments, it should be run from the program (`mccli`) directory, not the project directory, and it must be invoked with a dot: `. my.ps1`.  Users of other environments, such as the regular `MS-Windows command prompt`, will need to roll their own. Scripts on `Unix` should also be invoked with `. `; otherwise some of the definitions will not last after the script finishes.

The regular instructions appear below here.


### Installation
1. If it is not installed, download and install [Node.js](https://nodejs.org/) (known to  work with v6.5, but try the latest stable release)
2. If it is not installed, download and install [Python](https://www.python.org/downloads/) (known to work with v3.5.2, but try the the latest stable version)
3. ~~In the command line, install the montecarlo CLI by running `npm install -g @ecfairle/mccli` (this same command can be used to update to the latest version)~~
4. This should have installed some python libraries.  However, `pySide2` has many non-python dependencies.  If it is not set up properly, you should follow the instructions there.
   Currently they involve installing Qt5, which in turn has some requirements.  The clang components it needs are available for download from the Qt5 site and do not seem to be
   easily available from elsewhere.

Portions of the system currently rely on invoking python with the py command, which is Windows-specific.

### Initialization

Prerequisites:
   * `.inp` files in the current directory
   * a populated `input` directory
   * a `modfile` directory
   * Probably other stuff
   * Though probably not essential for this step, it would be good to put the model executable in the
     top-level directory.

Execute `mc init` (in command line within model directory) to initialize Montecarlo inputs:

1. default number of iterations
2. name of model executable
3. dat files (from modfile) to be varied
4. inp files to use   

creating folder structure as follows:
```
MC
└───inputs
        input_data.json
```
where `input_data.json` contains the initial data for montecarlo simulation.

#### Modfile setup
1. Copy files for simulation to corresponding montecarlo files using the naming convention `{name}_mc0.dat` (or `{name}_mc0.inp`) where *name* is the file name specified when choosing .dat/.inp files during `mc init`.
2. Add `_mc.dat` files to corresponding `.lst` files and increase the count of alternatives on the first line of the `.lst` file.
3. Change lines in `_mc0.inp` file to choose the appropriate line from the `.lst` file.
4. Create files with the same format as original model files but with standard deviations instead of means. These files use a similar naming convention: `{name}_sd.dat` (not for .inp files)

#### `.inp` file setup.

Then create `inp_distribution.txt` in directory `MC/inputs`, which should break down the .inp file variation into sections by keyword (indicating the lines to vary), e.g.:
```
HIEFFECT,1
   g=1,0.5477,0.02
MODEFFECT,1
   g=1,0.4,0.02
HICOSTAHA,6
   g=2, 0.0095, 0.0030, 0.0        #Myopathy
   g=3, 1.17, 0.15, 0.0            #Liver panel
   g=4, 7.30, 0.91, 0.0            #Doctor Visit
   g=5, 1.50, 0.47, 0.0            #Stroke
   g=6, 7.75, 3.00, 0.0            #Diabetes
   g=7, 148.30, 37.04, 0.0         #Statin, high intensity 
MODCOSTAHA,6
   g=2, 0.0095, 0.0030, 0.0        #Myopathy
   g=3, 1.17, 0.15, 0.0            #Liver panel
   g=4, 7.30, 0.91, 0.0            #Doctor Visit
   g=5, 1.50, 0.47, 0.0            #Stroke
   g=6, 7.75, 3.00, 0.0            #Diabetes
   g=7, 48.67, 12.17, 0.0          #Statin, moderate intensity 
STATINQALY,5
        0.000001, 0.0000005, 0.0     #Myopathy
        0.0000312, 0.00001560, 0.0   #Stroke
        0.0000747, 0.0000448, 0.0    #Diabetes
        0.0001, 0.000248, 0.0        #Unforeseen
        0.0, 0.0008, 0.0             #Pill disutility
```

The sections are further broken down by components, which each make up a part of their overall distribution. Here, sections include *HIEFFECT* (one component), *HICOSTAHA* (six components) etc.

##### Components
A section can consist of a single component but multiple components allows you to separate data in ways that aren't considered by the model itself. 

##### Distributions
The program will sample from distribution `dist_name` (normal if omitted) with parameters `mean, standard deviation` and sum the results from each line. The sum will replace the value on the lines in which `keyword` is found. Supported distributions are:

- **Normal** -  (with exception of using [mean option](#mean-option))
- **LogNormal** 
- **Beta**
- **Gamma**

##### Correlated Components
To indicate that samples should be correlated, give them the same group name (can be between labels). If a component shouldn't be correlated with any other component, either exclude the group argument or give it a unique group

##### Upper and Lower Bounds
Lower and/or upper bounds can be included but will default to -inf, +inf respectively. To add upper bound w/o lower bound put nothing inside lower_bound commas e.g. `mean,sd,,upper_bound`
The bounds censor the data, recoding out-of-bounds values to the boundary, rather than truncating data, which would simply drop the values out of bounds.  The mean and standard deviation for the distributions refers to the values before censoring.  The resulting variable will not have the mean and standard deviation given in the input parameters.

##### MEAN option

For normal distributions the `mean` parameter can be the literal **'MEAN'**, indicating the mean of the distribution should be determined by the line in the **.inp** file. In this case the second parameter, normally interpreted as the standard deviation, is interpreted as a coefficient of variation. The standard deviation will be the coefficient of variation times the mean.  This option is used to simplify the case in which there are many lines with the same significance but different means (these will be assumed to be correlated and have the same coefficient of variation).


```
    keyword,num_components 
    [g=group_name,][dist_name,]param1,param2,...[,lower_bound][,upper_bound]  
    [g=group_name,][dist_name,]param1,...   
    ... 
    [g=group_name,]...
 ```


## Running Simulations

Execute `mc run` to run the default number of simulations or `mc run n` to run n simulations. This creates a folder structure as follows:
```
MC
├───inputs
│       input_data.json
│       inp_distribution.txt
│
├───input_variation
│   │   inp.txt
│   │
│   └───dat_files
│           prfp_0.dat
│           prfp_1.dat
│           rsk_0.dat
│           rsk_1.dat
│
└───results
   │   .run
   │
   ├───breakdown
   │       0712_0.frmt
   │       0712_1.frmt
   │
   ├───cumulative
   │       0712_0.dat
   │       0712_1.dat
   │
   └───summary
           ageranges_1ST_MI.csv
           ageranges_95PLUS_LYRS.csv
           ageranges_CHD_DEATH.csv
           ageranges_DISC_LYRS.csv
           ageranges_DISC_NCVD$.csv
           ageranges_DISC_QALY.csv
           ageranges_DISC_TOT$.csv
           ageranges_DIS_DEINTERV$.csv
           ageranges_DIS_DHCHD$.csv
           ageranges_DIS_DHINTERV$.csv
           ageranges_DIS_DHSTR$.csv
           ageranges_INC_CHD.csv
           ageranges_INC_STROKE.csv
           ageranges_NCVD_DEATH.csv
           ageranges_PREV.csv
           ageranges_STROKE_DEATH.csv
           ageranges_TOT_DEATH.csv
           ageranges_TOT_MI.csv
           ageranges_TOT_STROKE.csv
```
Monte Carlo runs produce two output directories: `results` and `input_variation`. 

### Results
Directory `results` contains model outputs, including: 

1. *cumulative* results (copies of *outfile.dat*). Naming convention: `{name}_{simulation #}.dat`
2. *breakdown* results (rearranged data from *.out* file). Naming convention: `{name}_{simulation #}.frmt`
3. *summary* results (comma separated value files split up by outcome and organized by age-range and gender).

### Input Variation

Directory `input_variation` contains varied model inputs. These can be used to verify that inputs follow the desired distributions. In particular:

1. File `inp.txt` shows the ultimate value used to replace corresponding values in the *.inp* file (regardless if it's actually used). In addition, at the top it includes counts of the number of places in each *.inp* file the label is found.
2. Directory `dat_files` contains copies of the modified dat files (from modfile) for each run. Naming convention: `{name}_{simulation #}.dat`
