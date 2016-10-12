'use strict'
const shell = require("shelljs"),
			yargs = require("yargs"),
			colors = require('colors'),
			inquirer = require('inquirer'),
			fs = require('fs'),
			fsx = require('fs-extra'),
			path = require('path'),
			ProgressBar = require('progress'),
			files = require('./files');

let INPUTS_FILENAME = path.join('MC','inputs','input_data.json');

let error = (msg,stdout="") => {
	process.stdout.clearLine();
	process.stdout.cursorTo(0);
	console.log(`${'ERR'.bgYellow} ${msg}`);
	process.stdout.write(stdout);
	shell.exit(1);
};

let outFileName = (inp_file) => {
	let file_data = fs.readFileSync(`${inp_file}_mc0.inp`,'ascii');
	if (file_data.match(/(?:\r\n|\n)\S+\.out/)){
		return file_data.match(/(?:\r|\n)(\S+)(?=\.out)/)[1];
	}
};

module.exports = (argv) => {
	let simRuns = () => {
		let inputsFile = fs.readFileSync(INPUTS_FILENAME, 'utf8');

		let inputsData = JSON.parse(inputsFile);
		let ITERATIONS = 1000;

		if (argv.iterations) {
			ITERATIONS = argv.iterations;
		}
		else if (Number(argv._[0]) === argv._[0]) {
			ITERATIONS = argv._[0];
		}
		else {
			ITERATIONS = inputsData['default_iterations'];
		}

		let dat_files = inputsData['dat_files'].map((datfile) => datfile.filename)

		let inp_files = inputsData['inp_files'];
		inp_files = inp_files.filter( (file) => file.length > 0);

		let outputDirs = [
			'./MC/results',
			'./MC/results/breakdown',
			'./MC/results/cumulative',
			'./MC/results/summary',
			'./MC/input_variation'
		];

		for(let i = 0; i < outputDirs.length; i++){
			fsx.emptyDirSync(outputDirs[i]);
		}

		let bar = new ProgressBar(`  running simulations [:bar] :percent`, {
			    complete: '=',
			    incomplete: ' ',
			    width: 20,
			    total: ITERATIONS + 1
			  });

		let start = new Date();
		let res = null;
		for (let i = 0; i <= ITERATIONS; i++){
			let startIter = new Date();
			let lastTime = 0;

			if(i == 0) {
				res = shell.exec(`py ${__dirname}/../python/montecarlo.py -z -s`,{silent:true});
				if (res.code !== 0) {
					error("montecarlo.py run failed",res.stdout);
				}
			}
			else {
				let str = String(i + ' '.repeat(16));
				fs.appendFileSync('./MC/input_variation/inp.txt', str.substring(0,16) + '  ')
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

				let mcFile = `${inp_files[j]}_mc.inp`;

				if( !fs.existsSync(mcFile) ) {
					error(`Cannot find file ${mcFile}`);
				}

				let modelName = inputsData['model'];

				if ( i == 0 ) {
					res = shell.exec(`${modelName}<${mcFile}> MOD_zerorun.txt`,{silent:true});
				}
				else {
					res = shell.exec(`${modelName}<${mcFile}> nul`,{silent:true});
				}
				
				if (res.code !== 0) {
					error("Model run failed",res.stderr);
				}

				res = shell.exec(`py ${__dirname}/../python/format.py ${outfile}`,{silent:true});
				if (res.code !== 0) {
					error("format.py run failed",res.stdout);
				}

				let formattedFile = `${outfile}.frmt`;
				let formattedSaveFile = path.join('MC/results/breakdown',`${inp_files[j]}_${i}.frmt`);

				files.copy(formattedFile,formattedSaveFile);

				let outputSaveFile = path.join('MC/results/cumulative',`${inp_files[j]}_${i}.dat`); 
				files.copy('outfile.dat',outputSaveFile);

			}
			let endIter = new Date();

			lastTime = endIter.getTime() - startIter.getTime();
			process.stdout.clearLine();
			process.stdout.cursorTo(0);
			bar.update((i+1)/(ITERATIONS+1));
			if( i < ITERATIONS ){
				process.stdout.write(` eta:${parseFloat(lastTime*(ITERATIONS-i)/60000).toFixed(2)}m`);
			}	
		}

		res = shell.exec(`py ${__dirname}/../python/sum_results.py`,{silent:true});
		if (res.code !== 0) {
			error("sum_results.py run failed",res.stdout);
		}

		let end = new Date();
		let totalS = (end.getTime() - start.getTime())/1000;
		let hours = Math.floor(totalS / (60 * 60));
	  	let minutes = Math.floor(totalS / 60) % 60;
	  	let runData = {
			startTime: start.toLocaleString("en-US", {timeZone: "America/Los_Angeles"}),
			endTime: end.toLocaleString("en-US", {timeZone: "America/Los_Angeles"}),
			iterations: ITERATIONS,
			model: inputsData.model,
			inp_files: inputsData.inp_files,
			dat_files: inputsData.dat_files.map((fileData) => fileData.filename)
		};
		fs.appendFileSync('MC/results/.run',JSON.stringify(runData, null, 4));
		console.log(`  simulations completed in ${hours>0 ? hours + ' hours and ' : ''}${minutes} mintues!`.green)
		
	}

	
	if ( !fs.existsSync(INPUTS_FILENAME)) {
		error('cannot find inputs file','Run \'mc init\' to initialize Montecarlo files');
	}

	let saveFileDir = './MC/saved_runs';
	let resultsDir = './MC/results';
	if (fs.existsSync(resultsDir) && fs.readdirSync(path.join(resultsDir,'cumulative')).length !== 0) {
		console.log('  looks like there are already some montecarlo results stored'.bold);
		inquirer.prompt({
			type: 'confirm',
	    name: 'saveResults',
	    message: 'do you want to save these results? (otherwise they will be written over)',
	    default: true
		}).then( (answers) => {
			if (answers.saveResults) {
				inquirer.prompt({
					type: 'input',
			    name: 'saveDirectory',
			    message: 'enter name for this set of results',
			    default() {
			    	return new Date().toISOString().slice(0, -5).replace(/:/g,';');
			    }
				}).then( (answers) => {
						let runSaveDirectory = path.join(saveFileDir,answers.saveDirectory);
						fsx.ensureDirSync(runSaveDirectory);
						let resultsDirs = [
							'results',
							'input_variation'
						];
						for(let i = 0; i < resultsDirs.length; i++){
							fsx.copySync(path.join('./MC',resultsDirs[i]), path.join(runSaveDirectory,resultsDirs[i]));

						}
						console.log(`  last run stored in ${runSaveDirectory}`);
						simRuns();
				}).catch(err => {
						console.log(err)
				});
			}
			else {
				simRuns();
			}
		});
	}
	else {
		simRuns();
	}
}