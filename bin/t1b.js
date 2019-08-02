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

let INPUTS_FILENAME = path.join('MC', 'inputs', 'input_data.json');

let error = (msg, stdout = "") => {
    process.stdout.clearLine();
    process.stdout.cursorTo(0);
    console.log(`${'ERR'.bgYellow} ${msg}`);
    process.stdout.write(stdout);
    shell.exit(1);
};

let outFileName = (inp_file) => {
    let file_data = fs.readFileSync(`${inp_file}_mc0.inp`, 'ascii');
    if (file_data.match(/(?:\r\n|\n)\S+\.out/)) {
        return file_data.match(/(?:\r|\n)(\S+)(?=\.out)/)[1];
    }
};

module.exports = (argv) => {
    let simRuns = () => {
        // fails: no such file
        let inputsFile = fs.readFileSync(INPUTS_FILENAME, 'utf8');

        let inputsData = JSON.parse(inputsFile);

        if (argv.iterations) {
            var ITERATIONS = argv.iterations;
        }
        else if (Number(argv._[0]) === argv._[0]) {
            var ITERATIONS = argv._[0];
        }
        else {
            var ITERATIONS = inputsData['default_iterations'];
        }
        console.log(`  ${ITERATIONS} iterations starting at ${argv.start} with seed ${argv.seed} requested.`.green)

        let py = argv.py
        let dat_files = inputsData['dat_files'].map((datfile) => datfile.filename)

        let inp_files = inputsData['inp_files'];
        inp_files = inp_files.filter((file) => file.length > 0);

        let INP_OUTPUT_FILE = './MC/input_variation/inp.txt';


        //for (let j = 0; j < dat_files.length; j++) {
        //    let datfile = path.join('modfile', `${dat_files[j]}_mc.dat`);
        //    files.copy(datfile, `MC\\input_variation\\dat_files\\${dat_files[j]}_${i}.dat`);
        //}
        let j = 0;
        let i = 1;
        var xxx = `MC\\input_variation\\dat_files\\${dat_files[j]}_${i}.dat`;

        // for (let j = 0; j < inp_files.length; j++) {
        let outfile = outFileName(inp_files[j]);

        //   files.delete(`${outfile}.out`);

        let mcFile = `${inp_files[j]}_mc.inp`;

        if (!fs.existsSync(mcFile)) {
            error(`Cannot find file ${mcFile}`);
        }

        let modelName = inputsData['model'];

    }
    simRuns();
}