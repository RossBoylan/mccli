'use strict'
const shell = require("shelljs"),
    yargs = require("yargs"),
    colors = require('colors'),
    inquirer = require('inquirer'),
    fs = require('fs'),
    fsx = require('fs-extra'),
    path = require('path'),
    ProgressBar = require('progress'),
    files = require('./js/files');

module.exports = (argv) => {
    let simRuns = () => {
        let ITERATIONS = 1000;

        if (argv.iterations) {
            ITERATIONS = argv.iterations;
        }
        else if (Number(argv._[0]) === argv._[0]) {
            ITERATIONS = argv._[0];
        }
        console.log(`  ${ITERATIONS} iterations starting at ${argv.start} with seed ${argv.seed} requested.`.green)
    }

    

    simRuns();
}