'use strict';

const path = require('path');
year = 0;
age = 2;
sex = 3;
dataPath = path.join(".", "outputs")

module.exports = class SimDataSource {
   #patterns;
   #byvar;
   constructor(basename, ifname) {
      this.basename = basename.toLowerCase();
      this.ifname = ifname;
      this.ifpath = path.join(this.dataPath, ifname);
      this.#patterns = new Map(); // identify variables of interest
      this.#byvar = new Map(); // codebook, all variables
   }
   addPattern(text, regex) {
      this.#patterns.set(text.toLowerCase(), regex);
   }
   addVarDescription(varname, description){
      this.#byvar.set(varname.toLowerCase(), description);
   }
   countPatternMatches() {
      let pats = new Map(this.#patterns); // so deletions don't affect original;
      let result = new Map();
      let myvar = new Set(...this.#byvar.keys());
   
      const vs = [...pats]; // since we mutate pats
   
      // first check for exact matches
      for (const [txt, re] of vs) {
         if (myvar.has(txt)) {
            result.add(re, [1, [txt,]]);
            pats.delete(txt);
            myvar.delete(txt);
         }
      }
   
      // now check all that remain against the regexps
      // O(n^2) at least
      const p2 = [...pats];
      for (const [txt, re] of p2){
         // myvar is a Set, and therefore doen't have a filter method
         let matched = [];  // all matching variable names
         for (const v of myvar){
            if (re.test(v)){
               matched.push(v);
            }
         }
         // safer to delete after iteration
         // Set provide no set-level operator to remove members
         // experimental difference operator creates a new Set,
         // and is not currently in Node.js
         matched.forEach(v=>myvar.delete(v));
         // note we leave the pattern in pats
         result.add(re, [matched.length, matched]);
      }
   
      return result;
   }
   checkLostPatterns(counts){
      let missing = [];
      for (const xx of counts){
         let re, [count, vs] = xx;
         if (count==0)
            missing.push(re);
      }
      if (missing.length == 0)
         return;
      console.log("The following patterns in monte.conf don't match any variables.");
      error("Check for typos: "+missing.join(" "));
   }
   concreteVars(counts){
      let result = new Set();
      // likely the iterator will not support foreach
      counts.values().forEach(([n, vs])=>vs.forEach(v=>result.add(v)));
      return result;
   }
}
