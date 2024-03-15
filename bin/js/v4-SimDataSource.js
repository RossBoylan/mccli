'use strict';

const nReadLines = require('n-readlines'),
   path = require('path'),
   sqlite = require('better-sqlite3');
const { error } = require('./v4-logging');
const sep = ","; // used to split csv lines
const year = 0;
const age = 2;
const sex = 3;
const keyCols = [year, age, sex];
const dataPath = path.join(".", "outputs");

module.exports = class SimDataSource {
   #patterns;
   #byvar;
   constructor(basename, ifname) {
      this.basename = basename.toLowerCase();
      this.ifname = ifname;
      // this.dataPath does not resolve to the constant in this module
      // so just use the constant.
      this.ifpath = path.join(dataPath, ifname);
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

   prepare(master){
      this.counts = concretePatternMatches();
      checkLostPatterns(this.counts);
      this.allMatchingVars = concreteVars(this.counts);
   }
   
   read(master, iter, scenario){
      this.reader = nReadLines(this.ifpath);
      readHeader(master);
      readBody(iter);
   }
   
   readLine() {
      return this.reader.next().toString('ascii');
   }
   readHeader(master) {
      line = readLine();
      if (this.header){
         // we have already seen this file
         if (this.header != line){
            warning(`${this.ifpath} original header was ${this.header}`);
            warning(`But current file header is ${line}`);
            error("Mismatch.  Can not proceed safely.");
         }
      } else
         setupForHeader(master, line);
   }
   setupForHeader(master, line){
      this.header = line;
      this.interest = new Map();
      this.readCols = [];
      vs = line.split(sep);
      for (const [i, v] of vs.entries() ){
         if (keyCols.has(i) || this.allMatchingVars.has(v)) {
            this.interest.set(v, i);
            this.readCols.push(i);
         }
      }
      setupDatabase(master);
   }
   setupDatabase(master){
      if (!master.db)
         createSkeletonDB(master);
   }
   createSkeletonDB(master){
      this.dbFullPath = path.join(master.dbpath, master.dbfile);
      if (fs.existsSync(this.dbFullPath)){
         master.db = new sqlite(this.dbFullPath);
         // To Do: check if it has appropriate tables
         return;
      }
      master.db = new sqlite(this.dbFullPath);
      master.db.pragma('journal_mode = WAL');  //better-sqlite3 recommends this for performance
      makeDBTables(master);
      fillDemographicTables(master);
   }
   makeDBTables(master) {
      const db = master.db;
      db.transaction(() => {
           const design =  [
               ["variable", "varid integer primary key, name text, description text"],
               ["fullvar", "fullvarid integer primary key, varid references variable(varid), subCat text"],
               ["demo", "demoid integer primary key, label text, sex text, ageStart integer, ageEnd integer"],
               ["data", "scenario text, iSim integer, fullvarid references fullvar(fullvarid), "+
               "year integer, demoid references demo(demoid), value real"]
               ];
           for (const [tbl, cols] of design)
               db.exec(`CREATE TABLE IF NOT EXISTS ${tbl} (${cols});`);
           // serialization essential to ensure all tables exist before next step
           for (const indexStr of ["fullindex ON fullvar (varid, subCat)",
                                   "varindex ON variable (name)",
                                   "demoindex ON demo (label)",
                                   "demoid ON demo (demoid)"])
               db.exec(`CREATE UNIQUE INDEX IF NOT EXISTS ${indexStr};`);
       })();  //invoke transaction
   }
   fillDemographics(master) {
      // setup demographics
      const db = master.db;
      let demoid, ageEnd, label;
      let sql = db.prepare("INSERT INTO demo /*(demoid, label, sex, ageStart, ageEnd)*/ VALUES (?, ?, ?, ?, ?)");
      db.transaction(() => {
         // let not const in for() because I change the i* variables
         for (let [isex, sexname] of ["M", "F"].entries()) {
            // javascript is 0-based indexing, but we use 1 based
            isex += 1
            for (let [iage, ageStart] of [35, 45, 55, 65, 75, 85].entries()) {
                  iage += 1
                  demoid = 10*isex+iage;  // to ease future lookup
                  ageEnd = ageStart+9;
                  label = sexname+ageStart+"-"+ageEnd
                  sql.run(demoid, label, sexname, ageStart, ageEnd);
            }
         }})();  // () to run the function db.transaction produced
   }; 
}
