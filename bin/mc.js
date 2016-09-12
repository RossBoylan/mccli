#!/usr/bin/env node
'use strict';
var shell = require("shelljs"),
	yargs = require("yargs"),
	colors = require('colors'),
	fs = require('fs'),
	inquirer = require('inquirer'),
	path = require('path'),
	init = require('./init');

var ITERATIONS = 1000;

var outFileName = function(inp_file) {
	let file_data = fs.readFileSync(`${inp_file}.inp`,'ascii');
	if (file_data.match(/\w+\.out/)){
		return file_data.match(/\w+\.out/)[0];
	}
};

var argv = yargs.usage("$0 command")
.command("init", "initialize Montecarlo files", init)
.command("run-sims", "run Montecarlo simulations", function (yargs) {
	let dat_files = fs.readFileSync('MC/inputs/dat_files.txt','ascii').trim().split(/\r\n|\n/);
	let inp_files = fs.readFileSync('MC/inputs/inp_files.txt','ascii').trim().split(/\r\n|\n/);

	for (let i = 0; i < ITERATIONS; i++){
		if(i == 0) {
			if (shell.exec('py MC/scripts/montecarlo.py -z -s').code !== 0) {
				console.log("Error in montecarlo.py");
				shell.exit(1);
			}
		}
		else {
			if (shell.exec('py MC/scripts/montecarlo.py -s').code !== 0) {
				console.log("Error in montecarlo.py");
				shell.exit(1);
			}
		}

		for (let i = 0; i < dat_files.length; i++){
			let datfile = `${dat_files[i]}_mc.dat`;
			if(fs.existsSync(datfile)){
				fs.createReadStream(datfile).pipe(fs.createWriteStream(`MC/input_variation/dat_files/${dat_files[i]}`));
			}
		}

		for (let i = 0; i < inp_files.length; i++) {
			let outfile = outFileName(inp_files[i]);
			if(fs.existsSync(outfile)){
				fs.unlinkSync(outfile);
			}
			
			if (shell.exec(`CHDMOD90<${inp_files[i]}_mc.inp>junk.txt`).code !== 0) {
				console.log(`Error in CHDMOD90 on file ${inp_files[i]}`);
				shell.exit(1);
			}

			if (shell.exec(`py format.py ${outFileName}`).code !== 0) {
				console.log("Error in format.py");
				shell.exit(1);
			}

			let formattedFile = outFileName.replace('.out','.frmt');
			let formattedSaveFile = path.join('MC/results/breakdown',`${inp_files[i]}_${i}.frmt`);

			fs.createReadStream(formattedFile).pipe(fs.createWriteStream(formattedSaveFile));

			let outputSaveFile = path.join('MC/results/cumulative',`${inp_files[i]}_${i}.dat`); 
			fs.createReadStream('outfile.dat').pipe(fs.createWriteStream(outputSaveFile));

		}

		
	}
})
.usage('Usage: mc <command> [options]')
.demand(1, "You must provide a valid command. Did you mean 'mc run-sims'?")
.help("h")
.alias("h", "help")
.argv