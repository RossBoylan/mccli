var fs = require('fs'),
	shell = require('shelljs'),
	https = require('https');


module.exports = {
	fileError(fname) {
		console.log(`Cannot find file ${fname}`.red);
		console.log(`Run \'mc init\' to initialize files`);
		shell.exit(1);
	},

	delete(fname) {
		if(fs.existsSync(fname)){
			fs.unlinkSync(fname);
		}
	},

	copy(source, dest) {
		if(fs.existsSync(source)){
			fs.createReadStream(source).pipe(fs.createWriteStream(dest));
		}
	},

	appendFile(fname, str) {
		fs.appendFile(fname, str + '\n', function(err) {
		    if(err) {
		        return console.log(err);
		    }
		}); 
	},

	makeFile(fname) {
		fs.closeSync(fs.openSync(fname, 'w'));
	},

	makeDir(dirname) {
		if (!fs.existsSync(dirname)){
			fs.mkdirSync(dirname);
		}
	},

	readLines(fname) {
		if ( !fs.existsSync(fname) ) {
			fileError(fname);
		}
		return fs.readFileSync(fname,'ascii').trim().split(/\r\n|\n/);
	},

	download(dest, remote) {
		var destStream = fs.createWriteStream(dest);
		var request = https.get(remote, (res) => {
		  res.pipe(destStream);
		});
	},
}