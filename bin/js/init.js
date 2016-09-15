const colors = require('colors'),
			fs = require('fs'),
			inquirer = require('inquirer'),
			path = require('path'),
			files = require('./files'),
			https = require('https');

module.exports = (yargs) => {
	var dirs = [
		'./MC',
		'./MC/inputs',
	];

	for(var i = 0; i < dirs.length; i++){
		files.makeDir(dirs[i]);
	}

	files.download("MC/inputs/inp_variation.txt","https://raw.githubusercontent.com/ecfairle/CHD-Model/master/MC/inputs/inp_variation.txt");


	var datFileData = JSON.parse(fs.readFileSync(path.join(__dirname,'../input_data.json'), 'utf8'));
	var all_dat_files = datFileData['all_dat_files'];

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
	},
	{
		type: 'checkbox',
		message: 'select dat files to vary',
		name: 'chosen_files',
		choices: all_dat_files.map((file_data) => file_data.filename),
	},
	]).then((answers) => {
		if (answers.chosen_files.length < 1) {
			console.log('  Warning: no dat files selected'.yellow);
		}

		var inputsData = {
			default_iterations: answers.iterations,
			model: answers.model
		};
		inputsData['inp_files'] = [];
		inputsData['dat_files'] = [];
		for (var i = 0; i < answers.chosen_files.length; i++){
			inputsData['dat_files'].push(all_dat_files.filter((file) => file.filename == answers.chosen_files[i])[0]);

			var mc0File = path.join('modfile',`${answers.chosen_files[i]}_mc0.dat`);

			if ( !fs.existsSync(mc0File) ){
				console.log(`Creating ${mc0File}`);
				files.copy(path.join('modfile',`${answers.chosen_files[i]}.dat`),mc0File);
			}
		}

		var dir_files = fs.readdirSync('.');
		var all_inp_files = dir_files.filter(file => path.extname(file) == '.inp');
		all_inp_files = all_inp_files.map(file => file.slice(0,file.search(/[_\.]/)));
		all_inp_files = all_inp_files.filter((file, i) => all_inp_files.indexOf(file) == i);
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
					var mc0File = `${inp_files.chosen_files[i]}_mc0.inp`;
					if ( !fs.existsSync(mc0File) ){
						console.log(`Creating ${mc0File}`);

						fs.createReadStream(`${inp_files.chosen_files[i]}.inp`).pipe(fs.createWriteStream(mc0File));
					}
				}

				fs.writeFile('MC/inputs/input_data.json', JSON.stringify(inputsData,null,4), (err) => {
				  if (err) throw err;
				});
			});
		}
		else {
			console.log('  Warning: no inp files found'.yellow);
			fs.writeFile('MC/inputs/input_data.json', JSON.stringify(inputsData,null,4), (err) => {
			  if (err) throw err;
			});
		}
	});
}