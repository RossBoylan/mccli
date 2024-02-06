'use strict';

// class definitions
const VariableSelector = require('./v4-VariableSelector');
const Codebook = require('./v4-Codebook');

module.exports = (yargs)=> {
   let master = {};
   let vs = new VariableSelector(master, './__tests__/monte2.conf');
   let cb = new Codebook(master, './data/CVDPM_HF_Variable_List.csv');
   console.log(master.sources);

}
