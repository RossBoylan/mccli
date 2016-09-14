#!/usr/bin/env node
'use strict';
const yargs = require("yargs"),
		init = require('./js/init'),
		runSims = require('./js/runSims');

let argv = yargs.usage("$0 command")
.env('MY_PROGRAM')
.command("init", "initialize Montecarlo files")
.command("run-sims [iterations]", "run Montecarlo simulations")
.command("run [iterations]",false, "run Montecarlo simulations")
.command("r [iterations]", false,"run Montecarlo simulations")
.usage('Usage: mc <command> [options]')
.demand(1, "You must provide a valid command. Did you mean 'mc run-sims'?")
.recommendCommands()
.help("h")
.alias("h", "help")
argv = yargs.argv;
let command = argv._[0];


if (command == "run-sims" || command == "run" || command == "r" || String(command).trim() == '' || (Number(command) === command && command%1 == 0)){
	runSims(argv);
}
else if (command == "init") {
	init(yargs);
}
else {
	yargs.showHelp();
}