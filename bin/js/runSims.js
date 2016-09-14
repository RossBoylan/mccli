'use strict'
const shell = require("shelljs"),
			yargs = require("yargs"),
			colors = require('colors'),
			fs = require('fs'),
			path = require('path'),
			ProgressBar = require('progress'),
			files = require('./files');


var error = (msg,stdout="") => {
	process.stdout.clearLine();
	process.stdout.cursorTo(0);
	console.log(`${'ERR'.bgYellow} ${msg}`);
	process.stdout.write(stdout);
	shell.exit(1);
};

var outFileName = (inp_file) => {
	let file_data = fs.readFileSync(`${inp_file}_mc0.inp`,'ascii');
	if (file_data.match(/\w+\.out/)){
		return file_data.match(/(\w+)(?=\.out)/)[0];
	}
};

module.exports = (argv) => {
	var inputsFile = fs.readFileSync(path.join('MC/inputs','input_data.json'), 'utf8');

	if ( !inputsFile ) {
		error('cannot find inputs file.','Run \'mc init\' to initialize Montecarlo files');
	}

	var inputsData = JSON.parse(inputsFile);

	if (argv.iterations) {
		var ITERATIONS = argv.iterations;
	}
	else {
		var ITERATIONS = inputsData['default_iterations'];
	}

	let dat_files = inputsData['dat_files'].map((datfile) => datfile.filename)

	let inp_files = inputsData['inp_files'];
	inp_files = inp_files.filter( (file) => file.length > 0);

	var bar = new ProgressBar(`  running simulations [:bar] :percent`, {
		    complete: '=',
		    incomplete: ' ',
		    width: 20,
		    total: ITERATIONS
		  });

	var start = new Date();
	for (let i = 0; i < ITERATIONS; i++){
		var startIter = new Date();
		var lastTime = 0;

		var res = null;

		if(i == 0) {
			res = shell.exec(`py ${__dirname}/../python/montecarlo.py -z -s`,{silent:true});
			if (res.code !== 0) {
				error("montecarlo.py run failed",res.stdout);
			}
		}
		else {
			res = shell.exec(`py ${__dirname}/../python/montecarlo.py -s`,{silent:true});
			if (res.code !== 0) {
				error("montecarlo.py run failed",res.stdout);
			}
		}

		for (let j = 0; j < dat_files.length; j++){
			let datfile = path.join('modfile',`${dat_files[j]}_mc.dat`);
			files.copy(datfile,`MC\\input_variation\\dat_files\\${dat_files[j]}_${i}.dat`);
		}

		for (let j = 0; j < inp_files.length; j++) {
			let outfile = outFileName(inp_files[j]);

			files.delete(`${outfile}.out`);

			var mcFile = `${inp_files[j]}_mc.inp`;

			if( !fs.existsSync(mcFile) ) {
				error(`Cannot find file ${mcFile}`);
			}

			res = shell.exec(`CHDMOD90<${mcFile}> nul`);
			if (res.code !== 0) {
				error("Model run failed",res.stdout);
			}

			res = shell.exec(`py ${__dirname}/../python/format.py ${outfile}`);
			if (res.code !== 0) {
				error("format.py run failed",res.stdout);
			}

			let formattedFile = `${outfile}.frmt`;
			let formattedSaveFile = path.join('MC/results/breakdown',`${inp_files[j]}_${i}.frmt`);

			files.copy(formattedFile,formattedSaveFile);

			let outputSaveFile = path.join('MC/results/cumulative',`${inp_files[j]}_${i}.dat`); 
			files.copy('outfile.dat',outputSaveFile);

		}
		var endIter = new Date();

		lastTime = endIter.getTime() - startIter.getTime();
		process.stdout.clearLine();
		process.stdout.cursorTo(0);
		bar.update((i+1)/ITERATIONS);
		if( i < ITERATIONS - 1){
			process.stdout.write(` eta:${parseFloat(lastTime*(ITERATIONS-i-1)/60000).toFixed(2)}m`);
		}	
	}

	res = shell.exec(`py ${__dirname}/../python/sum_results.py`);
	if (res.code !== 0) {
		error("sum_results.py run failed",res.stdout);
	}

	var end = new Date();
	var totalS = (end.getTime() - start.getTime())/1000;
	var hours = Math.floor(totalS / (60 * 60));
  var minutes = Math.floor(totalS / 60) % 60;

	console.log(`  simulations completed in ${hours} hours and ${minutes} mintues!`.green)
}