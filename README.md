# Montecarlo CLI (Command Line Interface)

## Usage
```
Usage: mc <command> [options]

Commands:
  init                   initialize Montecarlo files
  run-sims [iterations]  run Montecarlo simulations

Options:
  -h, --help  Show help                                                [boolean]
```

## Getting Started

### Installation
1. Download [Nodejs v6.5](https://nodejs.org/download/release/v6.5.0/node-v6.5.0-x64.msi)
2. Download [Python v3.5.2](https://www.python.org/ftp/python/3.5.2/python-3.5.2-amd64.exe)
3. In the command line, install the montecarlo CLI by running `npm install -g @ecfairle/mccli`

### Initialization

#### MC INIT
Execute `mc init` (in command line within model directory) to initialize Montecarlo inputs:

1. default number of iterations
2. name of model executable
3. dat files (from modfile) to be varied
4. inp files to be varied

creating folder structure as follows:
```
MC
└───inputs
        input_data.json
```
where `input_data.json` contains the initial data for montecarlo simulation.

#### More Initialization
After programatic initialzation, you should:

1. Copy files for simulation to corresponding montecarlo files using the naming convention `{name}_mc0.dat` (or `{name}_mc0.inp) where 'name' is the file name specified when chossing .dat/.inp files during `mc init`.
2. Create files with the same format as original model files but with standard deviations instead of means. These files use a similar naming convention: `{name}_sd.dat` (not for .inp files)
3. Create inp_variation 
## Running Simulations
Execute `mc run` to run the default number of simulations or `mc run n` to run n simulations. 
```
MC
├───inputs
│       input_data.json
│       inp_variation.txt
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
