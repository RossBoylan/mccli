# GUI to summarize all runs in monte carlo, as gathered up by frmtToData.py

# Still to do:
# output to file
# user selectable input file and/or generation of same
# Is this actually the info and format desired? No
#    Target results/summary/ageranges_VVV.csv
#     If there are multiple scenarios they will appear as multiple
#     blocks with different filenames.
#    Note some values are reported with scientific notation now
# Wire up to recalc with change in stat selection
# Use all selected variables, not just the most recent click.
# Implement sd
# Output per simulation results

## allow MSVS "remote" debugging
import ptvsd
ptvsd.enable_attach()
ptvsd.wait_for_attach()

import pdb
import sys
import random
from PySide2 import QtCore, QtWidgets, QtGui, QtSql
from PySide2.QtSql import QSqlQuery
import pandas as pd
import numpy as np

DATABASE=r"C:\Users\rdboylan\Documents\KBD\bin\python\alldata.db"

class MyErr (Exception):
    pass

class MyWidget(QtWidgets.QWidget):
    def __init__(self, screenSize):
        super().__init__()
        if not self.getDatabase():
            raise MyErr("Unable to open database")

        self.text = QtWidgets.QLabel("CVD Model Result Disector")
        self.text.setAlignment(QtCore.Qt.AlignCenter)

        self.layout = QtWidgets.QVBoxLayout()

        self.layout.addWidget(self.text)
        
        self._initVariables()
        #self._initOptions()
        #self._initStats()
        #self._initResults()
        self.vVariables.selectionModel().selectionChanged.connect(self.variableSelectionChanged)
        self.setLayout(self.layout)

    def getDatabase(self):
        """set database connection and cursor
        return True on success
        eventually this will open a file picker"""
        # driver type is QtSql.QSqlDriver.SQLite
        self.db = QtSql.QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName(DATABASE)
        success =  self.db.open()
        drv = self.db.driver()
        return success

    def _initVariables(self):
        "setup data and view for list of variables"
        self.qVariables = QtSql.QSqlQueryModel()
        self.qVariables.setQuery("SELECT name, count(subCat) AS NSubGroups, group_concat(subcat, ' | ') as subGroups FROM "
                                    "fullvar LEFT OUTER JOIN variable USING (varid) "
                                    "GROUP BY varid ORDER BY name;")
        #self.qVariables.setQuery("SELECT name FROM variable ORDER BY name;")
        #print("Result of query: {}".format(self.qVariables.lastError()))
        self.vVariables = QtWidgets.QTableView()
        self.vVariables.setModel(self.qVariables)
        self.vVariables.resizeColumnsToContents()
        self.layout.addWidget(self.vVariables)

    def _initOptions(self):
        "Setup option GUI and data"
        self.vOptionGroup = QtWidgets.QGroupBox("Subgroups to break out")
        innerLayout = QtWidgets.QHBoxLayout()
        opts = [("age", True), ("sex", True), ("year", False) ]
        self._opts = {}
        for fld, default in opts:
            cb = QtWidgets.QCheckBox(fld)
            cb.setChecked(default)
            innerLayout.addWidget(cb)
            self._opts[fld] = cb
        self.vOptionGroup.setLayout(innerLayout)
        self.layout.addWidget(self.vOptionGroup)

    def _initStats(self):
        "setup GUI and data for statistics to collect"
        self.vStatsGroup = QtWidgets.QGroupBox("Values to Report")
        innerLayout = QtWidgets.QHBoxLayout()
        opts = [("", True), ("avg", True), ("sd", False), ("min", True), ("max", True) ]
        self._stats = {}
        for fld, default in opts:
            cb = QtWidgets.QCheckBox(fld)
            cb.setChecked(default)
            innerLayout.addWidget(cb)
            self._stats[fld] = cb
        self.vStatsGroup.setLayout(innerLayout)
        self.layout.addWidget(self.vStatsGroup)

    def _initResults(self):
        "setup GUI for results, though it will be empty at the start"
        self.vResults = QtWidgets.QTableView()
        self.qResults = QtSql.QSqlQueryModel()
        self.vResults.setModel(self.qResults)
        self.layout.addWidget(self.vResults)
        
    def variableSelectionChanged(self, selected, deselected):
        """User has selected a new variable.  For now just show most recent one.
        Compute results and display them.
        The arguments are <QItemSelection>s"""
        # selected.indexes() returns QModelIndexList, which is iterable yielding QModelIndex
        vars = [idx.data() for idx in selected.indexes()]
        self._buildResults2(vars)

    def _buildResults2(self, vars):
        """Build custom report in expected format and display it.
        Within simulation, sum over all years.
        Then rotate results so sex/age are columns.
        Compute subtotals over sex and then overall.
        Compute statistics by column.
        Finally, append per simulation values.
        vars is a list of strings, names of top level variables"""
        vars = "('" +  "', '".join(vars) + "')"
        groupVars = ["name", "subCat", "scenario", "iSim", "label"]
        sqlGroups = ", ".join(groupVars)
        strSQL = "SELECT "+sqlGroups+", TOTAL(value) as v" +\
         " FROM data LEFT OUTER JOIN fullvar USING (fullvarid) LEFT OUTER JOIN variable " + \
            "USING (varid) LEFT OUTER JOIN demo USING (demoid) " +\
            " WHERE name IN " + vars + " GROUP BY "+sqlGroups +" ORDER BY "+ sqlGroups + ";"
        print(strSQL)
        q = QSqlQuery()
        if not q.exec_("CREATE TEMP VIEW allyrs AS " + strSQL):
            raise MyErr("Unable to create temp allyrs: "+q.lastError().text())
        q2 = QSqlQuery()
        if not q2.exec_("SELECT DISTINCT label FROM allyrs ORDER BY label;"):
            raise MyErr("Unable to count demographics from temp allyrs: "+q2.lastError().text())
        # q.size seems to always be -1
        labels = []
        while q2.next():
            labels.append(q2.value(0))
        nDemo = len(labels)

        q = QSqlQuery()
        q.setForwardOnly(True)
        if not q.exec_("SELECT * FROM allyrs;"):
            print(q.lastError())
            return
        # at this point we have v with totals across years
        colNames = labels
        self.df = pd.DataFrame(self._chunk(q, labels), columns=colNames)
        self._addTotals()
        self._addStats()
        #self.df.to_string(float_format=(lambda a : np.format_float_positional(a, precision=2)))
        print(self.df)
        return self.df

    def _chunk(self, q, labels):
        """Rotate entries for one chunk and return a DataFrame.
        q is a query result with the necessary data
        labels are the column labels
        a chunk is one particular variable, subCat, and scenario"""
        chunkValues = None
        t_row = [ ]  # transposed row
        iSim = -1
        last_label = labels[len(labels)-1]
        while q.next():
            thisKeys = [q.value(i) for i in range(3)]
            if chunkValues:
                if not chunkValues == thisKeys:
                    # new chunk.  For now we just bail
                    return
            else:
                chunkValues = thisKeys
            if iSim < 0:
                # start of this row
                iSim = q.value(3)
                if iSim>5:
                    # shortcut for development
                    return
                t_row = [ ]
            t_row.append(q.value(5))
            if q.value(4) == last_label:
                # one transposed row is ready
                yield t_row
                iSim = -1

    def _addTotals(self) :
          """add columns with totals for both sexes and overall.
          The self.df is modified in place """
          self._addMF('F')
          self._addMF('M')
          self._addAll()

    def _addMF(self, sex):
        cnms = self.df.columns
        idx = [i for i in range(len(cnms)) if (cnms[i].startswith(sex) and cnms[i][1].isdigit())]
        self.df.insert(self.df.shape[1], sex+" (all)", self.df.iloc[:, idx].sum(axis=1))

    def _addAll(self):
        ncol = self.df.shape[1]
        # iloc arguments must be [] not ()
        self.df.insert(ncol, "Everyone", self.df.iloc[:, [ncol-2, ncol-1]].sum(axis=1))


    def _addStats(self):
        """Compute requested statistics for self.df
        and insert them at the top of same"""
        # for now ignore requested stats and just give all
        aSumDF = self.df.describe(percentiles=(0.05, .10, .25, .5, .75, .9, .95), include=[np.number])
        self.df = pd.concat([aSumDF, self.df])




    def _buildResults(self, vars):
        """Build a results query and show it in vResults
        vars is a list of strings, names of top level variables"""
        vars = "('" +  "', '".join(vars) + "')"
        print(vars)

        # build list of group variables, in order
        groupVars = ["name", "subCat"]
        picked = set( [ key for key, widget in self._opts.items() if widget.isChecked()])
        fulldemo = frozenset(("age", "sex"))
        if fulldemo <= picked:
            groupVars.append("label")
            picked -= fulldemo
        else:
            onedemo = picked & fulldemo
            if onedemo:
                picked -= onedemo
                onedemo = onedemo.pop()
                if onedemo == "age":
                    onedemo="ageStart"
                groupVars.append(onedemo)
        if picked:
            # must be year
            groupVars.append("year")
        
        # build list of statistics
        stats = [ key for key, widget in self._stats.items() if widget.isChecked()]

        # put it all together
        sqlGroups = ", ".join(groupVars)
        strSQL = "SELECT "+sqlGroups
        for s in stats:
            strSQL += ", {0}(value) AS {0}".format(s)
        strSQL += " FROM data LEFT OUTER JOIN fullvar USING (fullvarid) LEFT OUTER JOIN variable " + \
            "USING (varid) LEFT OUTER JOIN demo USING (demoid) " +\
            " WHERE name IN " + vars + " GROUP BY "+sqlGroups +" ORDER BY "+ sqlGroups + ";"
        print(strSQL)
        self.qResults.setQuery(strSQL)
        print(self.qResults.lastError())
        # maybe need to refresh display?
        
if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    screenSize = app.primaryScreen().availableSize()
    widget = MyWidget(screenSize)
    tableSize = QtCore.QSize(screenSize.width()*0.6, screenSize.height()*0.6)
    widget.resize(tableSize)
    #widget.resize(800, 600)
    #widget.adjustSize()
    widget.show()


    sys.exit(app.exec_())
