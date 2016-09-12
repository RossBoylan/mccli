var colors = require('colors'),
	fs = require('fs'),
	inquirer = require('inquirer'),
	path = require('path'),
	files = require('./files'),
	http = require('http');

module.exports = (yargs) => {
	var dirs = [
		'./MC',
		'./MC/inputs',
		'./MC/results',
		'./MC/results/breakdown',
		'./MC/results/cumulative',
		'./MC/input_variation',
	];

	for(var i = 0; i < dirs.length; i++){
		files.makeDir(dirs[i]);
	}

	var file = fs.createWriteStream("MC/scripts/montecarlo.py");
	var request = http.get("http://raw.githubusercontent.com/ecfairle/CHD-Model/master/montecarlo.py", function(response) {
	  response.pipe(file);
	});

	var file = fs.createWriteStream("MC/scripts/format.py");
	var request = http.get("http://raw.githubusercontent.com/ecfairle/CHD-Model/master/format.py", function(response) {
	  response.pipe(file);
	});

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
		message: 'Enter number of iterations for montecarlo simulations',
		name: 'interations',
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
		message: 'Select dat files to vary',
		name: 'chosen_files',
		choices: all_dat_files,
	},
	]).then((dat_files) => {
		if (dat_files.chosen_files.length < 1) {
			console.log('  Warning: no dat files selected'.yellow);
		}

		var dat_prefix_file = "./MC/inputs/dat_files.txt";

		files.makeFile(dat_prefix_file);
		for (var i = 0; i < dat_files.chosen_files.length; i++){
			files.appendFile(dat_prefix_file,dat_files.chosen_files[i]);
		}


		var inp_prefix_file = "./MC/inputs/inp_files.txt";
		files.makeFile(inp_prefix_file);

		var dir_files = fs.readdirSync('.');
		var all_inp_files = dir_files.filter(file => path.extname(file) == '.inp');
		all_inp_files = all_inp_files.map(file => file.slice(0,-4));

		if (all_inp_files.length > 0){
			inquirer.prompt([
			{
				type: 'checkbox',
				message: 'Select inp files to vary',
				name: 'chosen_files',
				choices: all_inp_files,
			}
			]).then((inp_files) => {
				for (var i = 0; i < inp_files.chosen_files.length; i++){
					files.appendFile(inp_prefix_file, inp_files.chosen_files[i]);
					fs.createReadStream(`${inp_files.chosen_files[i]}.inp`).pipe(fs.createWriteStream(`${inp_files.chosen_files[i]}_mc0.inp`));
				}
			});
		}
		else {
			console.log('  Warning: no inp files found'.yellow)
		}
	});
}