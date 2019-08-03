# convert .frmt file to database
# For now just explore the parsing

import re
import sqlite3

expectCols = "M35-44             M45-54             M55-64             M65-74             M75-84             M85-94             " \
    "F35-44             F45-54             F55-64             F65-74             F75-84             F85-94             "
expectColStart =  "Year     " + expectCols

blankRE = re.compile(r"^\s*$")
datRE = re.compile(r"^(19|20)\d\d\s{4}")
standardRE = re.compile(r"^(Year     M35-44             M45-54             M55-64             M65-74             M75-84             M85-94             F35-44             F45-54             F55-64             F65-74             F75-84             F85-94             |"+
        r"\s*Age/Sex Breakdown$)")                
h2RE = re.compile(r"\s{9,}(\S+(\s{1,3}\S+)*)")

def header2(line):
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
        print("Subheads: ", r)
        return r
    else:
        return None
    
def examine(fn, top=100):
    i = 0
    state = 0  # scan for variable name
    with open(fn, "rt") as fin:
        for line in fin:
            if top and i>=top:
                break
            i += 1
            if state == 0:
                varname = line.strip()
                state = 1
            elif state == 1:
                #sub heads
                if blankRE.match(line):
                    print("%s has an empty line after it. Skipping.".format(varname))
                    state = 0
                    continue
                colgroups = header2(line)
                if colgroups:
                    firstSet = colgroups[0][1]
                    if firstSet == varname or firstSet == "Age/Sex Breakdown":
                        colgroups[0] = (colgroups[0][0], None)
                    else:
                        pass
                state = 2
            elif state==2:
                #individual column headings
                assert line.startswith(expectColStart)
                oldStart = 0
                if colgroups:
                    for iStart, subvar in colgroups:
                        if oldStart > 9:
                            assert line[oldStart:iStart] == expectCols
                        oldStart = iStart
                    # trim trailing newline
                    assert line[oldStart:(len(line)-1)] == expectCols
                state = 3
            elif state == 3:
                "individual data lines"
                if blankRE.match(line):
                    state = 0
                    continue
                year = line[:4]
                if colgroups:
                    iOld = 0
                    oldSub = None
                    for iStart, subvar in colgroups:
                        if iOld and oldSub != "TBD":
                            vs = line[iOld:iStart].split()
                            print("{}:{}:{}:{}".format(varname, oldSub, year, vs))
                        iOld = iStart
                        oldSub = subvar
                    # fall through to get last group
                else:
                    iOld = 9
                    oldSub = None
                vs = line[iOld:].split()
                print("{}:{}:{}:{}".format(varname, oldSub, year, vs))

            #print(i, len(line), line, end="")

def makeTable(d):
    "Create database tables in d, a cursor"
    design = [("batch", "batchid integer primary key, production bool, description text, start text, end text"),
              ("variable", "varid integer primary key, name text, description text"),
              ("demo", "demoid integer primary key, sex text, ageStart integer, ageEnd integer"),
              ("data", "batchid references batch(batchid), varid references variable(varid), "
               "subvarid references variable(varid), demoid references demo(demoid), "
               "year integer, value real")
              ]
    for tbl, cols in design:
        d.execute("CREATE TABLE {} ({});".format(tbl, cols))

if False:  
    conn = sqlite3.connect(":memory:")
    curs = conn.cursor()
    makeTable(curs)
    x = curs.execute("select demoid from demo where sex=? and ageStart=?;", ("F", 35))
    y = curs.fetchone()
    conn.close()


examine(r"C:\Users\rdboylan\Documents\KBD\A. Mod91_mexPA_MCs_06.28.2019\intermediate0\P06_mc.frmt",
        top=50)
           