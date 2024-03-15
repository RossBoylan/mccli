#!/usr/bin/env node
'use strict';
// The yargs documentation shows require('yargs/yargs').
const yargs = require("yargs"),
		init = require('./js/init'),
		runSims = require('./js/runSims'),
        path = require('node:path'),
        v4 = require('./js/v4')

let argv = yargs
.command({
    command: 'v4',
    aliases: ['test'],
    desc: 'test v4 processing',
    handler: v4
})
.command({
    command: 'init',
    desc: 'initialize MC system in current directory',
    handler: init
    })
.command({
    command: 'run-sims [iterations] [start] [seed]',
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
.option('continue', {
    describe: "continue interrupted run, using parameters from before, not from the command line.",
    alias: ['resume', 'cont'],
    boolean: true  /* RB: Docs unclear what the value does */
})
.option('dbfile', {
    describe: "name of database file to record simulation results. Use with run.",
    default: 'hfmc_results.sqlite',
    type: 'string'
})
.option('dbpath', {
    describe: "directory in which to put database. Use with run.",
    default: path.join(".", "MC", "results"),
    type: "string"
})
.help()
.argv
