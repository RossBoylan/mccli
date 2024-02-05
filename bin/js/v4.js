'use strict';

// class definitions
const VariableSelector = require('./v4-VariableSelector');

module.exports = (yargs)=> {
   let master = {};
   let vs = new VariableSelector(master, './__tests__/monte2.conf');
   console.log(master.sources);

}
