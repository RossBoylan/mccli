var fs = fs = require('fs');

module.exports = {
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
	}
}