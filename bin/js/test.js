const inquirer = require('inquirer');
console.log("Hi\n");
let file_data = {
    filename: "myfile"
};
let x = {
    value: file_data.filename,
    name: file_data.filename + ": DANGEROUS",
    description: "Changes to "+ file_data.filename + 
        " ordinarily require manual calibration.",
    };	
//var x = "myfile"; // even simpler test
var all_dat_files = [
    {filename: "myfile",
        danger: true
    },
    {filename: "ordinary"
    }
]
var whichDatFiles = {
		type: 'checkbox',
		message: 'select dat files to vary',
		name: 'dat_files',
		choices: all_dat_files.map((file_data) => {
			if (file_data.danger){
				return {
				value: file_data.filename,
				name: file_data.filename + ": DANGEROUS",
				description: "Changes to "+ file_data.filename + 
				  " ordinarily require manual calibration.",
				};
			} else {
				return file_data.filename;
			}
		}),
	};
var questions = [ whichDatFiles ];
inquirer.prompt(questions).then((answers) => {
    console.log("got responses ")
    console.log(answers.dat_files)
});
