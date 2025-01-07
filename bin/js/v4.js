'use strict';

// class definitions
const VariableSelector = require('./v4-VariableSelector');
const Codebook = require('./v4-Codebook');

class Master {
   constructor(yargs) {
      this.dbpath = yargs.dbpath;
      this.dbfile = yargs.dbfile;
      let vs = new VariableSelector(this, './__tests__/monte2.conf');
      let cb = new Codebook(this, './data/CVDPM_HF_Variable_List.csv');
      console.log(this.sources);
   }
   iterate(i, scenario=""){
      this.db.transaction(()=> {
         for (const sds in this.sources.values()){
            sds.read(this, i, scenario)
         }
      })();
   }
   done() {
      SimDataSource.done(this)
   }
}

module.exports = (yargs)=> {
   return new Master(yargs);
}
