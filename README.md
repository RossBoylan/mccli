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

#### .inp file setup
Create files with the same format as original model files but with standard deviations instead of means. These files use a similar naming convention: `{name}_sd.dat` (not for .inp files).

Then create `inp_distribution.txt`, which should break down the .inp file variation by keyword (indicating the lines to vary), e.g.:
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

Here, the labels include *HIEFFECT*, *MODEFFECT* etc. and each are further broken down by components.

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

For normal distributions `param1` can simply be **'MEAN'**, indicating the mean of the distribution should be determined by the line in the **.inp** file. Here, `param2` must be a coefficient of variation. This option is used to simplify the case in which there are many lines with the same significance but different means (these should clearly be correlated and have the same coefficient of variation).


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
