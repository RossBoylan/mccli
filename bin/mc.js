#!/usr/bin/env node
'use strict';
const yargs = require("yargs"),
		init = require('./js/init'),
		runSims = require('./js/runSims')

let argv = yargs
.command({
    command: 'init',
    desc: 'initialize MC system in this directory',
    handler: init
  })
.command({
    command: 'run-sims [iterations]',
    aliases: ['run', 'r'],
    desc: 'run MC simulations',
    handler: runSims
	}).argv