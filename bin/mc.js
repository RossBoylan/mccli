#!/usr/bin/env node
'use strict';
const yargs = require("yargs"),
		init = require('./js/init'),
		runSims = require('./js/runSims')

let argv = yargs
.command({
    command: 'init',
    desc: 'initialize MC system in current directory',
    handler: init
    })
.command({
    // the command string must include positional arguments for them
    // to be parsed properly. 
    command: 'run-sims [iterations] [start] [seed] [--json] [--overwrite]',
    aliases: ['run', 'r'],
    desc: 'run MC simulations',
    // yargs >= 17.0.0 allows positional at root level
    // so it might be possible to lift some of these calls URLSearchParams.
    builder: (yargs) => yargs.positional('iterations', {
        describe: 'Number of simulations to perform',
        type: 'number',
        default: 1000
    })
        .positional('start', {
            describe: "Number of first simulation.  Simulations will range from start to start+iterations-1",
            type: 'number',
            default: 0
        })
        .positional('seed', {
            describe: 'seed for random number generator.  Will be combined with simulation number.  ' +
                'If omitted random numbers will not be reproducible, may not be sufficiently independent' +
                ' across simulations, and may stall the simulation and other processes by exhausting system entropy.',
            type: 'number'
        })
        .option('json', {
            describe: 'Format output using JSON, ordinarily for use by another program.  All to stdout.  '+
            'All objects have a type, one of PROGRESS (simulation progress), '+
            'SUMMARY (after all sims complete), DETAIL (details of all simulations), '+
            'DONE (very last message), or ERR (error).  All have a text field with the main message, '+
            'and some have additional fields.  See code for details.  '+
            'Note that programs invoked by run-sims will still generate non-JSON output on stdout and, '+
            'possibly, stderr.',
            boolean: true
        })
        .option('overwrite', {
            describe: 'Overwrite existing results *without* notice.',
            type: 'boolean',
            default: false
        })
        .epilog("All numbers should be unsigned integers."),
    handler: runSims,
})
.option('python', {
    decribe: "command to invoke python.  May include a path or options.",
    alias: 'py',
    default: 'py',
    defaultDescription: 'py probably only works on MS-Windows',
    type: 'string'
})
.help()
.argv
