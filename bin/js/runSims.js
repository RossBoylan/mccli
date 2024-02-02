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
let PROGRESS_FILENAME = path.join('MC', '.progress')
let SIM_FILENAME = path.join('MC', '.simStart')

const error = require('./error');

let outFileName = (inp_file) => {
	let file_data = fs.readFileSync(`${inp_file}_mc0.inp`,'ascii');
	if (file_data.match(/(?:\r\n|\n)\S+\.out/)){
		return file_data.match(/(?:\r|\n)(\S+)(?=\.out)/)[1];
	}
};

let startup_ordinary = (argv) => {
	/* Handle startup in the usual case, rather than an interrupted run */

	/* Check if there appears to be a previous run.  Note this function is only called
	when the user did *not* specify --continue, i.e., they don't think there was an interrupted
	run. So the only choices are to save the previous results or overwrite them. */
	let saveFileDir = './MC/saved_runs';
	let resultsDir = './MC/results';
	if (fs.existsSync(resultsDir) && fs.readdirSync(path.join(resultsDir,'cumulative')).length !== 0) {
		inquirer.prompt({
			type: 'confirm',
	    name: 'saveResults',
	    message: 'There are previous results.  Do you want to save them? (otherwise they will be written over)',
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
				}).catch(err => {
						console.log(err)
				});
			}
		});
	}

	/* Clear the output directories, creating the necessary subdirectories.
	We always do this in this function. */
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
}

let startup_resume = (argv) => {
	/* A previous run was interrupted and we wish to continue.
	The main difficulty is cleaning up stuff that may have been written
	in the last, partial run. */

	/* TODO
	write stuff to PROGRESS_FILENAME elsewhere in code
	check for existence of it and SIM_FILENAME
	check integrity of PROGRESS_FILENAME.
	figure out how to integrate the info into argv
	any other info needs to go back in main routine?
	main routine may need to bypass some setup processing, figuring i0, i1
	check consistency inputsData in simSpec and one acquired normally?
		could just use this info in place of the normal acquisition
	stamp out remnants of potentially interrupted run
	maybe --cautious would toss last n "good" results as well
	check if command line options inconsistent with previous run? or check if they are present at all?
	*/
	var pfile = fs.readFileSync(PROGRESS_FILENAME, 'utf8');
	var progress = JSON.parse(pfile, 'utf8');
	var simFile = fs.readFileSync(SIM_FILENAME, 'utf8');
	simSpec = JSON.parse(simFile);

}

let startup_check = (argv) => {
	if ( !fs.existsSync(INPUTS_FILENAME)) {
		error('cannot find inputs file','Run \'mc init\' to initialize Montecarlo files');
	}
	if (fs.existsSync(PROGRESS_FILENAME)){
		if (!argv.continue) {
			error(`Apparent interrupted run.  Either specify --continue or delete ${PROGRESS_FILENAME}.`);
		return startup_resume(argv);
		}
	}
	if (argv.continue){
		error(`--continue specified but ${PROGRESS_FILENAME} not present. Aborting.`);
	}
	return startup_ordinary(argv);
}

module.exports = (argv) => {
	let simRuns = () => {
		startup_check(argv);
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


		let start = new Date();
        let res = null;
        let i0 = argv.start
        let i1 = ITERATIONS+i0-1

		// in case job is interrupted
		let runData = {
			/* RB: Unsure why timeZone is wired in, but keeping it for consistency
			with existing uses toward the bottom of this function. */
			startTime: start.toLocaleString("en-US", {timeZone: "America/Los_Angeles"}),
			status: "started",
			i0: i0,
			i1: i1,
			argv: argv,
			inputsData: inputsData
		};

		fs.writeFileSync(SIM_FILENAME, JSON.stringify(runData, null, 4));


		for (let i = i0; i <= i1; i++){

			let startIter = new Date();
			let lastTime = 0;

			if(i == 0) {
				let cmd = py+` ${__dirname}/../python/montecarlo.py -z -s`;
				res = shell.exec(cmd, {silent:true});
				if (res.code !== 0) {
					error(`montecarlo.py run failed: ${cmd}`,res.stdout);
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
					error(`montecarlo.py run failed: ${cmd}`,res.stderr);
				}
			}

			for (let j = 0; j < dat_files.length; j++){
				let baseName = `${dat_files[j]}_mc.dat`;
				let datFile = path.join('modfile', baseName);
				files.copy(datFile, `MC\\input_variation\\dat_files\\${dat_files[j]}_${i}.dat`);
				if (baseName.length > 12) {
					/* Fortran has not had a 12 character limit on filenames for a long time 
					 * (since Fortran-66, says Larry).  Larry says our program allows very long
					 * filenames, but the version I see imposes the limit both in defining the lengths
					 * of filename variables and in input formats (e.g., Subs.f90).  So filenames
					 * are effectively truncated at 12 characters. We provide a name in that format so
					 * the Fortran model can find the inputs.
					 * 
					 * If such truncation renders names non-unique this strategy will fail.  
					 * 
					 * When the Fortran model completely supports long filenames AND we are not 
					 * interested in running simulations with older models, remove this whole if block.
					 * 
					 * --Ross Boylan
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
				let cmd = `${modelName}<${mcFile}> `

				if ( i == 0 ) {
					cmd += `MOD_zerorun.txt`;
					res = shell.exec(cmd,{silent:true});
				}
				else {
					/* The use of nul below may be MS-Windows specific.
					Unix uses /dev/null.  But shelljs may translate.
					Ross Boylan
					*/
					cmd += `nul`;
					res = shell.exec(cmd ,{silent:true});
				}
				
				if (res.code !== 0) {
					error(`Model run failed: ${cmd}`, res.stderr);
				}

				cmd = py+` ${__dirname}/../python/format.py ${outfile}`;
				res = shell.exec(cmd,{silent:true});
				if (res.code !== 0) {
					error(`${cmd} run failed`, res.stdout);
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
		let cmd = py+` ${__dirname}/../python/sum_results.py`;
		res = shell.exec(cmd, {silent:true});
		if (res.code !== 0) {
			error(`${cmd} run failed`,res.stderr);
		}
		console.log('done')

		let end = new Date();
		let totalS = (end.getTime() - start.getTime())/1000;
		let hours = Math.floor(totalS / (60 * 60));
	  	let minutes = Math.floor(totalS / 60) % 60;
	  	runData = {
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
		fs.rmSync(SIM_FILENAME);
		console.log(`  simulations completed in ${hours>0 ? hours + ' hours and ' : ''}${minutes} minutes!`.green)
		
	}

	simRuns();

}
