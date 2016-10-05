const colors = require('colors'),
			fs = require('fs'),
			inquirer = require('inquirer'),
			path = require('path'),
			files = require('./files'),
			https = require('https');

var questions = [
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
		type: 'input',
		message: 'name of model executable',
		name: 'model',
		default() {
			return 'CHDMOD90';
		},
		validate(modelName) {
			if(fs.existsSync(`${modelName}.exe`)){
				return true;
			}
			else {
				return 'file not found in current directory';
			}
		}
	}
];

module.exports = (yargs) => {
	var dirs = [
		'./MC',
		'./MC/inputs',
	];

	for(var i = 0; i < dirs.length; i++){
		files.makeDir(dirs[i]);
	}

	var datFileData = JSON.parse(fs.readFileSync(path.join(__dirname,'../input_data.json'), 'utf8'));
	var all_dat_files = datFileData['all_dat_files'];

	var whichDatFiles = {
		type: 'checkbox',
		message: 'select dat files to vary',
		name: 'dat_files',
		choices: all_dat_files.map((file_data) => file_data.filename),
	};

	questions.push(whichDatFiles);

	var dir_files = fs.readdirSync('.');
	var all_inp_files = dir_files.filter(file => path.extname(file) == '.inp');
	all_inp_files = all_inp_files.map(file => file.slice(0,file.search(/_mc|\./)));
	all_inp_files = all_inp_files.filter((file, i) => all_inp_files.indexOf(file) == i);

	var whichInpFiles = {
		type: 'checkbox',
		message: 'select inp files to use',
		name: 'inp_files',
		choices: all_inp_files,
		validate(inp_files) {
			if (inp_files.length < 1) {
				return 'you must choose at least one inp file';
			}
			return true;
		}
	};

	if (all_inp_files.length > 0) {
		questions.push(whichInpFiles);
	}
	else {
		console.log('  Error: no inp files found'.red);
		process.exit(1);
	}

	inquirer.prompt(questions).then((answers) => {
		if (answers.dat_files.length < 1) {
			console.log('  Warning: no dat files selected'.yellow);
		}

		var inputsData = {
			default_iterations: answers.iterations,
			model: answers.model
		};
		inputsData['inp_files'] = [];
		inputsData['dat_files'] = [];
		for (var i = 0; i < answers.dat_files.length; i++){
			inputsData['dat_files'].push(all_dat_files.filter((file) => file.filename == answers.dat_files[i])[0]);
		}

		for (var i = 0; i < answers.inp_files.length; i++){
			inputsData['inp_files'].push(answers.inp_files[i]);
		}

		fs.writeFile('MC/inputs/input_data.json', JSON.stringify(inputsData,null,4), (err) => {
		  if (err) throw err;
		});

		var nextSteps = 'Next steps: \n \
	1) make standard deviation files for the dat files you wish to vary using the same format as their corresponding mean file \n \
	2) add an inp_variation.txt file to MC/inputs if you want to vary .inp files (follow instructions from link) \n \n \
More in depth instructions can be found at https://github.com/ecfairle/mccli'.bold;

		console.log(nextSteps)
	});
}