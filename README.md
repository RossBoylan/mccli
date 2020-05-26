# Montecarlo CLI (Command Line Interface)

WARNING: v 3.0 changes the meaning of inputs for the lognormal distribution.
The mean and standard deviation now refer to the mean and the sd of the random
variable being generated.  This is the same as for every other distribution.

Recall that Y has a log-normal distribution if X = log(Y) has a normal distribution.
The old interpretation was that the mean and sd referred to X; under the new scheme they
refer to Y. If a and b are the mean and sd of the normal, and m and s are the mean and sd
of the log-normal, they are related by
    m = exp(a+b^2/2)
    s^2 = (exp(b^2)-1)exp(2a+b^2).
So, if you're being mechanical, the old a and b must be changed to the new m and s.
However, that exercise might reveal that the old values weren't sensible, in which 
case a rethink would be in order.

There are other more subtle changes to the handling of correlated random numbers.  The old code was
ineffective in inducing correlations for beta, and possibly log-normal, distributions.  The new
code should generally induce higher correlations, though they will necessarily be imperfect.

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

This code is the `repeatable` branch of RossBoylan/mccli on github.com.  Despite that, it is still identified as "@ecfairle/mccli",
and because of that the conventional installation with npm install may not work, especially if you have already installed the earlier version.

I recommend putting a copy of this package on your local hard drive, e.g., `Documents\mccli`.  You can clone it from github and switch to the `repeatable` branch,
or get it from an archive file.

To ensure setup, you should
`npm install -g colors fs fs-extra inquirer path progress shelljs single-line-log yargs` 
if you are on a new machine.  If you have a previous `mccli` installation they should all be present.

If you are not in a python virtual environment, which is recommended,
and you do not have administrative rights, you should add the `--user` option at the end of the 
pip commands given next.
`py -m pip install numpy matplotlib randomgen`
If you already had an install,
`py -m pip install randomgen`
should suffice.  This code requires recent versions of numpy and randomgen, and so even if you have
them installed you should
`py -m pip install numpy randomgen --upgrade`

You need either a current `randomgen` (1.18+) or an older one
(possibly 1.14).  A required function was dropped from the library in
between.  1.16 will not work.  Also note that `randomgen` is being
incorporated into `NumPy` 1.17+.  Likely there will be future
adjustments required, and `randomgen` may become unnecessary.  See
https://pypi.org/project/randomgen/ and https://github.com/bashtage/randomgen.

Then, assuming you have this package in `Documents\mccli`, model file in `Documents\mymodel`, and you are in the latter directory, type
`node ..\mccli\bin\mc init`
to set it up and
`node ..\mccli\bin\mc run <nsims> <first index> <seed>`
e.g., `node ..\mccli\bin\mc run 5 0 8093218` to run 5 simulations starting at 0.  Index 0 is special because it uses the original parameters.

`node ..\mccli\bin\mc --help` for more information, and
`node ..\mccli\bin\mc run --help` for even more information on the `run` command.

If you're curious, the reason for using `node <path to main file>` instead of just `mc` is that `mc` only works because it was registered as a global
shortcut by `npm install`, which these instructions deliberately avoid using.  To be sure of getting the right version we invoke `node` directly and give it the location of the file
to execute.

The regular instructions appear below here.


### Installation
1. If it is not installed, download and install [Node.js](https://nodejs.org/) (known to  work with v6.5, but try the latest stable release)
2. If it is not installed, download and install [Python](https://www.python.org/downloads/) (known to work with v3.5.2, but try the the latest stable version)
3. In the command line, install the montecarlo CLI by running `npm install -g @ecfairle/mccli` (this same command can be used to update to the latest version)
4. This should have installed some python libraries.  However, pySide2 has many non-python dependencies.  If it is not set up properly, you should follow the instructions there.
   Currently they involve installing Qt5, which in turn has some requirements.  The clang components it needs are available for download from the Qt5 site and do not seem to be
   easily available from elsewhere.

Portions of the system currently rely on invoking python with the py command, which is probably Windows-specific.

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
1. Copy files for simulation to corresponding montecarlo files using the naming convention `{name}_mc0.dat` (or `{name}_mc0.inp`) where *name* is the file name specified when chossing .dat/.inp files during `mc init`.
2. Add _mc.dat files to corresponding .lst files and change lines in _mc0.inp file to choose the apporopriate line from the .lst file.
3. Create files with the same format as original model files but with standard deviations instead of means. These files use a similar naming convention: `{name}_sd.dat` (not for .inp files)

#### .inp file setup.

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
The program will sample from distribution `dist_name` (normal if omitted) with parameters `param1,param2,...` and sum the results from each line. The sum will replace the value on the lines in which `keyword` is found. Supported distributions are:

- **Normal** - `param1`: mean, `param2`: standard deviation (with exception of using [mean option](#mean-option))
- **LogNormal** - `param1`: mean, `param2`: standard deviation 
- **Beta** - `param1`: alpha, `param2`: beta
- **Gamma** - `param1`: shape, `param2`: scale

##### Correlated Components
To indicate that samples should be correlated, give them the same group name (can be between labels). If a component shouldn't be correlated with any other component, either exclude the group argument or give it a unique group

##### Upper and Lower Bounds
Lower and/or upper bounds can be included but will default to -inf, +inf respectively. To add upper bound w/o lower bound put nothing inside lower_bound commas e.g. `param1,param2,,upper_bound`

##### MEAN option

For normal distributions `param1` can simply be **'MEAN'**, indicating the mean of the distribution should be determined by the line in the **.inp** file. Here, `param2` must be a coefficient of variation. This option is used to simplify the case in which there are many lines with the same significance but different means (these will be assumed to be correlated and have the same coefficient of variation).


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
