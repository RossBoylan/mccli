var colors = require('colors'),
	fs = require('fs'),
	inquirer = require('inquirer'),
	path = require('path'),
	files = require('./files'),
	https = require('https');

module.exports = (yargs) => {
	var dirs = [
		'./MC',
		'./MC/inputs',
		'./MC/results',
		'./MC/results/breakdown',
		'./MC/results/cumulative',
		'./MC/input_variation',
		'./MC/scripts'
	];

	for(var i = 0; i < dirs.length; i++){
		files.makeDir(dirs[i]);
	}

	files.download("MC/scripts/montecarlo.py","https://raw.githubusercontent.com/ecfairle/CHD-Model/master/montecarlo.py");
	files.download("MC/scripts/format.py","https://raw.githubusercontent.com/ecfairle/CHD-Model/master/format.py");
	files.download("MC/inputs/inp_variation.txt","https://raw.githubusercontent.com/ecfairle/CHD-Model/master/MC/inputs/inp_variation.txt");

	var all_dat_files = [
		'b',
		'bdia',
		'bstk',
		'inc',
		'incdia',
		'incstk',
		'cst',
	];

	inquirer.prompt([
	{
		type: 'input',
		message: 'default number of iterations',
		name: 'iterations',
		default() {
			return '1000';
		},
		validate(str) {
			if(/^\+?(0|[1-9]\d*)$/.test(str)){
				return true;
			}
			else {
				return 'Number of iterations must be positive integer';
			}
		},
		filter(str) {
			return Number(str);
		}
	},
	{
		type: 'checkbox',
		message: 'select dat files to vary',
		name: 'chosen_files',
		choices: all_dat_files,
	},
	]).then((answers) => {
		var inputsData = {
			"iterations": answers.iterations
		};

		if (answers.chosen_files.length < 1) {
			console.log('  Warning: no dat files selected'.yellow);
		}

		var dat_prefix_file = "./MC/inputs/dat_files.txt";

		files.makeFile(dat_prefix_file);
		inputsData['dat_files'] = [];
		inputsData['inp_files'] = [];
		for (var i = 0; i < answers.chosen_files.length; i++){
			files.appendFile(dat_prefix_file,answers.chosen_files[i]);
			inputsData['dat_files'].push(answers.chosen_files[i]);
		}


		var inp_prefix_file = "./MC/inputs/inp_files.txt";
		files.makeFile(inp_prefix_file);

		var dir_files = fs.readdirSync('.');
		var all_inp_files = dir_files.filter(file => path.extname(file) == '.inp' && file.search('_mc') == -1);
		all_inp_files = all_inp_files.map(file => file.slice(0,-4));

		if (all_inp_files.length > 0){
			inquirer.prompt([
			{
				type: 'checkbox',
				message: 'select inp files to vary',
				name: 'chosen_files',
				choices: all_inp_files,
			}
			]).then((inp_files) => {
				for (var i = 0; i < inp_files.chosen_files.length; i++){
					inputsData['inp_files'].push(inp_files.chosen_files[i]);
					files.appendFile(inp_prefix_file, inp_files.chosen_files[i]);
					var mc0File = `${inp_files.chosen_files[i]}_mc0.inp`;
					if ( !fs.existsSync(mc0File) ){
						console.log(`Creating ${inp_files.chosen_files[i]}_mc0.inp`);

						fs.createReadStream(`${inp_files.chosen_files[i]}.inp`).pipe(fs.createWriteStream(mc0File));
					}
				}
			});
		}
		else {
			console.log('  Warning: no inp files found'.yellow)
		}
	});
}