# convert .frmt file to database
# For now just explore the parsing

import os.path
from pathlib import Path
import re
import sqlite3
from datetime import datetime
now = datetime.now

expectCols = "M35-44             M45-54             M55-64             M65-74             M75-84             M85-94             " \
    "F35-44             F45-54             F55-64             F65-74             F75-84             F85-94             "
expectColStart =  "Year     " + expectCols

blankRE = re.compile(r"^\s*$")
datRE = re.compile(r"^(19|20)\d\d\s{4}")
standardRE = re.compile(r"^(Year     M35-44             M45-54             M55-64             M65-74             M75-84             M85-94             F35-44             F45-54             F55-64             F65-74             F75-84             F85-94             |"+
        r"\s*Age/Sex Breakdown$)")                
h2RE = re.compile(r"\s{9,}(\S+(\s{1,3}\S+)*)")

class WeirdFName(Exception):
    def __init__(self, fname):
        self.fname = fname

class FrmtDir:
    "represent a directory with .frmt files"
    def __init__(self, dir, dbase, top, notifyInterval=100):
        """dir is a path like object
        dbase is the name of the database backend"""
        pathDB = Path(dbase)
        if pathDB.exists():
            pathDB.unlink()
        self._dir = Path(dir)
        assert self._dir.is_dir()
        files = self._dir.glob("*.frmt")
        self._conn = sqlite3.connect(dbase)
        self._c = self._conn.cursor()
        makeTable(self._c)
        self._vs = Variables(self._c)
        self._fvs = FullVars(self._c)
        self._notifyInterval = notifyInterval
        self._scan(files, top)
        self._conn.commit()

    def _scan(self, files, top):
        tstart = now()
        print("Starting scan at {}".format(tstart))
        nfiles = 0
        for file in files:
            try:
                ff = FrmtFile(file, self._vs, self._fvs, self._c)
                ff.examine(top=top, notifyInterval=self._notifyInterval)
                nfiles += 1
            except WeirdFName as wf:
                print("Skipping {} (non-conformant name)".format(wf.fname))
        tend = now()
        print("Finished {} files at {} after {} seconds.".format(nfiles, tend, (tend-tend).total_seconds()))
            
class FrmtFile:
    "parse a format file and put results in database"
    fnameRE = re.compile(r"([^_]+)_(\d+)\.frmt")

    def __init__(self, fn, vs, fullvs, cursor):
        """fn <str|path> the file to parse
        vs <Variables> table of variables
        fullvs <FullVars> table of variable, subcategory
        cursor  cursor for the database"""
        self._fn = fn
        base = os.path.basename(fn)
        m = FrmtFile.fnameRE.match(base)
        if not m:
            raise WeirdFName(base)
        self._stem = m.group(1)
        self.iSim = int(m.group(2))
        self._c = cursor
        self._vs = vs
        self._fullvs = fullvs


    def header2(self, line):
        """Check if line appears to have 2nd level headers.
        Return None if not, else a list of (position, header)"""
        if len(line)<100:
            return None
        iPos = 0
        r = []
        while True:
            m = h2RE.search(line, iPos)
            if m:
                r.append( (m.start(1), m.group(1)) )
                iPos = m.end(1)+1
            else:
                break
        if len(r)>1:
            # a single field is not multiple columns
            #print("Subheads: ", r)
            return r
        else:
            return None
    
    def examine(self, top=100, notifyInterval=100):
        if notifyInterval and self.iSim % notifyInterval == 0:
            self._c.execute("SELECT count(*) as n FROM data;")
            r = self._c.fetchone()[0]
            print("iSim {}, data rows {} at {}".format(self.iSim, r, now()))
        i = 0
        state = 0  # scan for variable name
        with open(self._fn, "rt") as fin:
            for line in fin:
                if top and i>=top:
                    break
                i += 1
                if state == 0:
                    varname = line.strip()
                    varid = self._vs.id(varname)
                    state = 1
                elif state == 1:
                    #sub heads
                    if blankRE.match(line):
                        if self.iSim == 0:
                            print("{} on line {} has an empty line after it. Skipping.".format(varname, i))
                        state = 0
                        continue
                    colgroups = self.header2(line)
                    if colgroups:
                        subVars = []  # list of (iPost, varID)
                        for iStart, subName in colgroups:
                            if subName == varname or subName == "Age/Sex Breakdown":
                                subVars.append( (iStart, None) )
                            else:
                                subVars.append( (iStart, subName) )
                    else:
                        subVars = None
                    state = 2
                elif state==2:
                    #individual column headings
                    assert line.startswith(expectColStart)
                    oldStart = 0
                    if subVars:
                        for iStart, subvar in subVars:
                            if oldStart > 9:
                                assert line[oldStart:iStart] == expectCols
                            oldStart = iStart
                        # trim trailing newline
                        assert line[oldStart:(len(line)-1)] == expectCols
                    state = 3
                elif state == 3:
                    "individual data lines"
                    if blankRE.match(line):
                        # presumed end of subtable
                        state = 0
                        continue
                    year = line[:4]
                    if subVars:
                        iOld = 0
                        oldSub = None
                        for iStart, subvar in subVars:
                            if iOld:
                                self.acceptData(varid, oldSub, year, line[iOld:iStart] )
                            iOld = iStart
                            oldSub = subvar
                        # fall through to get last group
                    else:
                        iOld = 9
                        oldSub = None
                    self.acceptData(varid, oldSub, year, line[iOld:] )

    def acceptData(self, varid, subvar, year, text):
        "Process and record one chunk of data relating to a single subvar"
        if subvar == "TBD":
            # these seem to have no useful info are duplicated
            return
        fullVarid = self._fullvs.id(varid, subvar)
        xs = text.split()
        demoid = 1
        for x in xs:
            self._c.execute("INSERT INTO data VALUES (?, ?, ?, ?, ?, ?);",
                            (self._stem, self.iSim, fullVarid, year, demoid, x))
            demoid += 1

def makeTable(d):
    "Create database tables in d, a cursor"
    design = [
              ("variable", "varid integer primary key, name text, description text"),
              ("fullvar", "fullvarid integer primary key, varid references variable(varid), subCat text"),
              ("demo", "demoid integer primary key, label text, sex text, ageStart integer, ageEnd integer"),
              ("data", "scenario text, iSim integer, fullvarid references fullvar(fullvarid), "
               "year integer, demoid references demo(demoid), value real")
              ]
    for tbl, cols in design:
        d.execute("CREATE TABLE {} ({});".format(tbl, cols))
    for indexStr in ("fullindex ON fullvar (varid, subCat)",
                     "varindex ON variable (name)",
                     "demoindex ON demo (label)"):
        d.execute("CREATE UNIQUE INDEX {};".format(indexStr))
    # populate demographics
    i=1
    for label in expectCols.split():
        d.execute("INSERT INTO demo VALUES (?, ?, ?, ?, ?);", (i, label, label[0], label[1:3], label[4:6]))
        i += 1

class Variables:
    "Return rowid of variable, creating if necessary.  May cache"
    def __init__(self, cursor):
        self._c = cursor
 
    def id(self, varname):
        self._c.execute("SELECT varid FROM variable WHERE name=?;", (varname, ))
        r = self._c.fetchone()
        if r:
            return r[0]
        else:
            x = self._c.execute("INSERT INTO variable (name) VALUES (?);", (varname, ))
            self._c.execute("SELECT varid FROM variable WHERE name=?;", (varname, ))
            r = self._c.fetchone()
            return r[0]


class FullVars:
    "return rowid of full variable/subvariable specification, creating as needed"
    def __init__(self, cursor):
        self._c = cursor
        self._cacheargs = None
        self._cacheval = None

    def id(self, varid, subCat):
        myargs = (varid, subCat)
        if self._cacheargs == myargs:
            return self._cacheval
        self._cacheargs = myargs
        if subCat == None:
            subCat = "-"
        self._c.execute("SELECT fullvarid FROM fullvar WHERE varid=? AND subCat=?;", (varid, subCat))
        r = self._c.fetchone()
        if not r:
            x = self._c.execute("INSERT INTO fullvar (varid, subCat) VALUES (?, ?);", (varid, subCat))
            self._c.execute("SELECT fullvarid FROM fullvar WHERE varid=? AND subCat=?;", (varid, subCat))
            r = self._c.fetchone()
        self._cacheval = r[0]
        return self._cacheval
    
if True:  
    fdir = FrmtDir(r"C:\Users\rdboylan\Documents\KBD2\MC_P2012 1000 runs\results\breakdown",
                   "allData.db", top= None, notifyInterval=100)
    #              C:\Users\rdboylan\Documents\KBD\A. Mod91_mexPA_MCs_06.28.2019\intermediate0"
    fdir._c.execute("SELECT COUNT(*) AS NDataRows FROM data;")
    r = fdir._c.fetchone()
    print("Total data rows = {}".format(r[0]))
    fdir._c.execute("SELECT data.*, variable.name, demo.label FROM data LEFT JOIN fullvar USING (fullvarid) "
                    "LEFT JOIN variable USING (varid) LEFT JOIN demo USING (demoid) LIMIT 10;")
    for r in fdir._c:
        print(r)

    # when source was :memory: this just hung
    #c2=sqlite3.Connection("alldata.db")
    #fdir._conn.backup(c2, pages=10)

    input("Hit enter to exit")

    #c2.close()
    fdir._conn.close()
