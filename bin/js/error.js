'use strict'
const shell = require("shelljs");

module.exports = (msg,stdout="") => {
	process.stdout.clearLine();
	process.stdout.cursorTo(0);
	console.log(`${'ERR'.bgYellow} ${msg}`);
	process.stdout.write(stdout);
	shell.exit(1);
};
