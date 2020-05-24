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

		if (argv.iterations) {
			var ITERATIONS = argv.iterations;
		}
		else if (Number(argv._[0]) === argv._[0]) {
			var ITERATIONS = argv._[0];
		}
		else {
			var ITERATIONS = inputsData['default_iterations'];
		}

        let py = argv.py
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

		let start = new Date();
        let res = null;
        let i0 = argv.start
        let i1 = ITERATIONS+i0-1
		for (let i = i0; i <= i1; i++){

			let startIter = new Date();
			let lastTime = 0;

			if(i == 0) {
				res = shell.exec(py+` ${__dirname}/../python/montecarlo.py -z -s`,{silent:true});
				if (res.code !== 0) {
					error("montecarlo.py run failed",res.stdout);
				}
			}
			else {
				let str = String(i + ' '.repeat(16));
				let INP_OUTPUT_FILE = './MC/input_variation/inp.txt';
				if (fs.existsSync(INP_OUTPUT_FILE)) {
					fs.appendFileSync(INP_OUTPUT_FILE, str.substring(0,16) + '  ')
                }
                let cmd = py + ` ${__dirname}/../python/montecarlo.py -s -i ${i}`
                if (argv.seed)
                    cmd += ` --seed ${argv.seed}`
				res = shell.exec(cmd,{silent:true});
				if (res.code !== 0) {
					error("montecarlo.py run failed",res.stderr);
				}
			}

			for (let j = 0; j < dat_files.length; j++){
				let baseName = `${dat_files[j]}_mc.dat`;
				let datFile = path.join('modfile', baseName);
				files.copy(datFile, `MC\\input_variation\\dat_files\\${dat_files[j]}_${i}.dat`);
				if (baseName.length > 12) {
					/* The fortran program assumes file names are 12 characters max,
					 * truncating all names that are longer.  So that it can find the inputs,
					 * we provide a name in that format.
					 * If such truncation renders names non-unique this strategy will fail.  RB
					 */
					let shortFile = path.join('modfile', baseName.substring(0, 12));
					/* On windows the links seem to behave like hardlinks, and so they must be
					refreshed each time.  RB
					*/
					if (fs.existsSync(shortFile)) {
						fs.unlinkSync(shortFile);
                    }
					fs.linkSync(datFile, shortFile);
                }
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

				res = shell.exec(py+` ${__dirname}/../python/format.py ${outfile}`,{silent:true});
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
			if( i < i1 ){
				process.stdout.write(`simulations remaining: ${i1-i} eta:${parseFloat(lastTime*(i1-i)/60000).toFixed(2)}m`);
			}	
		}

		console.log('sum results')
		res = shell.exec(py+` ${__dirname}/../python/sum_results.py`,{silent:true});
		if (res.code !== 0) {
			error("sum_results.py run failed",res.stderr);
		}
		console.log('done')

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
                dat_files: inputsData.dat_files.map((fileData) => fileData.filename),
                i0: i0,
                i1: i1,
            seed: argv.seed
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
