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
      setupDatabase();
      console.log(this.sources);
   }
   setupDatabase(){
      // this should only be called once, but just in case
      if (!this.db)
         createSkeletonDB();
   }
   createSkeletonDB(){
      this.dbFullPath = path.join(this.dbpath, this.dbfile);
      existingDB = fs.existsSync(this.dbFullPath)
      this.db = new sqlite(this.dbFullPath);
      this.db.pragma('journal_mode = WAL');  //better-sqlite3 recommends this for performance
      if (existingDB) {
         // To Do: check if it has appropriate tables
         return;
      }
      this.db.transaction( () => {
         makeDBTables();
         fillDemographicTables();
      }).();
   }
   makeDBTables() {
      const db = this.db;
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
   }
   fillDemographics() {
      // setup demographics
      const db = this.db;
      let demoid, ageEnd, label;
      let sql = db.prepare("INSERT INTO demo /*(demoid, label, sex, ageStart, ageEnd)*/ VALUES (?, ?, ?, ?, ?)");
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
      }
   };
   iterate(i, scenario=""){
      this.db.transaction(()=> {
         for (const sds in this.sources.values()){
            sds.read(this, i, scenario)
         }
      })();
   }
   done(){
      let db = this.db;
      if (db === undefined){
         return;
      }
      db.close();
      delete this.db;
   }
}

module.exports = (yargs)=> {
   return new Master(yargs);
}
