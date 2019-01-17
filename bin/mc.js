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
    command: 'run-sims [iterations] [start] [seed]',
    aliases: ['run', 'r'],
    desc: 'run MC simulations',
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
                'If omitted random numbers will not be reproducible, and may not be sufficiently independent' +
                ' across simulations.',
            type: 'number'
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
