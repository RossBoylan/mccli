'use strict';
const nReadLines = require("n-readlines");
//const error = require('./error');

const lineRE = /^(\w+),(\w+\$?),\s*([^,]*)\s*,\s*$/;
function realname(short){
   if (short == "targets")
      return "targets_output";
   return short;
}

module.exports = class Codebook {
   constructor(master, codebookPath){
      const reader = new nReadLines(codebookPath);
      let line = reader.next(); // skip first line with headers
      let x, section, vname, des;  // will hold the match
      while (line=reader.next()){
         x = line.toString('ascii').match(lineRE);
         if (!x){
            line = line.toString('ascii');
            continue;
         }
         [x, section, vname, des] = line.toString('ascii').match(lineRE);
         if (section != this.section){
            // New section in codebook
            // Currently nothing to do to close previous section
            // this.sds will be undefined if there is no entry, i.e., not of interest
            this.section = section;
            this.sds = master.sources.get(realname(section));
         }
         if (this.sds) {
            if (! des)
               des = vname;
            this.sds.addVarDescription(vname, des);
         }
      }
   }
}
