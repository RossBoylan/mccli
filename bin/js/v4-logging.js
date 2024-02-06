'use strict'
const shell = require("shelljs");

function warning(msg) {
   console.log("WARNING: "+msg);
}

function error(msg,stdout=""){
	process.stdout.clearLine();
	process.stdout.cursorTo(0);
	console.log(`${'ERR'.bgYellow} ${msg}`);
	process.stdout.write(stdout);
	shell.exit(1);
};

exports.error = error;
exports.warning = warning;
