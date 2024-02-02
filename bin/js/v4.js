'use strict';

// class definitions
const VariableSelector = require('./v4-VariableSelector');

module.exports = (yargs)=> {
   let master = {};
   let vs = new VariableSelector(master, './py_tests/monte.conf');
   console.log(master.sources);

}
