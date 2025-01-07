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
         // Set provides no set-level operator to remove members
         // difference operator creates a new Set,
         // available in  Node.js as of v22
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
      readBody(master, iter, scenario);
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
      this.interest = [];
      vs = line.split(sep);
      for (const [i, v] of vs.entries() ){
         if (this.allMatchingVars.has(v)) {
            this.interest.push({name: v, icol: i});
         }
      }
      setupDatabase(master);
   }
   setupDatabase(master){
      defineVariablesInDB(master);
   }
   defineVariablesInDB(master){
      const hasVarSQL = master.db.prepare("SELECT varid FROM variable WHERE name=?")
      const hasFullVarSQL = master.db.prepare("SELECT fullvarid FROM fullvar WHERE varid=?")
      const insertVarSQL = master.db.prepare("INSERT INTO variable (name, description) VALUES (?, ?)")
      const insertFullVarSQL = master.db.prepare("INSERT INTO fullvar (varid) VALUES (?)")
      for (const varinfo of this.interest){
         if (r = hasVarSQL.get(v)){
            //already defined. assume OK
            varinfo.varid = r.varid;
            r = hasFullVarSQL.get(varinfo.varid);
            varinfo.fullvarid = r.fullvarid
            continue;
         }
         info = insertVarSQL.run(v, this.#byvar.get(v.toLowerCase()))
         if (info.changes != 1)
            // API says it throws errors if something goes wrong
            // so I don't know if this is necessary
            error(`Error inserting ${v} into table named variable`)
         varinfo.varid = info.lastInsertRowid
   
         // assume that if there is no entry in variable there is none in fullvar
         info = insertFullVarSQL.run(varinfo.varid)
         if (info.changes != 1)
            error(`Error inserting ${v} into table named fullvar`)
         varinfo.fullvarid = info.lastInsertRowid
      }
   }
   readBody(master, iteration, scenario){
      // skip scenario column since I have nothing for it
      const sql = master.db.prepare(`INSERT INTO data (iSim, scenario, fullvarid,
           year, demoid, value) VALUES (?, ?, ?, ?, ?, ?)`);
      let line;
      while (line = readLine().trim()){
         // strip trailing ,
         if (line.at(-1)==',')
               line = line.slice(0, -1);
         const xs = line.split(/\s*,\s*|\s+/);
         // without parseInt the next line does string appends
         const demoid = parseInt(xs[age]) + 10*parseInt(xs[sex]);
         const iyr =  parseInt(xs[year]);
         for (const varinfo of this.interest) {
               // parseFloat probably makes no difference because of SQLite `type affinity`
               // will attempt to convert an input string to a float for this column
            sql.run(iteration, scenario, varinfo.fullvarid, iyr, demoid, xs[varinfo.icol]); // parseFloat(xs[varinfo.icol]));
            }
      }
   }
}
