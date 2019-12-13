
# GUI to summarize all runs in monte carlo, as gathered up by frmtToData.py
# File: frmtReport.py
# Author: Ross Boylan
# Created: 2019-09-12

# INPUTS
#    One file with a SQLite database produced by frmtToData.py
#    By default, allData.db in the current directory, but
#    user specifiable. MyWidget.inName has the value.
#
# OUTPUTS
#   ageranges_VVV_SSS.csv in the format produced by the Fortran program for some variables
#               already.  VVV is the variable description and SSS is the subcategory (e.g.,
#               DE or DH). _SSS will be absent for the primary outcome for VVV.
#               These go in the current directory by default, but you can reset that in the 
#               GUI.  MyWidget.outDir has the current output path.
#               VVV_SSS will have any "/", as in Dead/Alive replace by " or " since Python on
#               windows will not write files with "/" as a part of a name.
#               If there are multiple scenarios they will be appended one after the other in the csv
#               file, with the "file" column distinguishing them (as in the Fortran output).

# DEPENDENCIES
# This program requires PySide2, pandas and numpy to run.  They in turn have other dependencies.
# In particular, see https://doc.qt.io/qtforpython/gettingstarted.html says to install 
# libclang first, as well as a recent python.
# This was developed with Python 3.7 64 bit; I encountered problems with the 32 bit version.
# In general, to install python modules on Windows, use
# py -m pip install <list of modules>.  For example
# py -m pip install pyside2 numpy pandas
# You may find that the command pip3 or pip works without the py -m.
# If you have multiple versions of python installed you can select the one to run with, e.g.,
# py -3-64
# meaning run the most recent version of Python 3 that is 64 bit.
#
# 
# OPERATION
# First you should run frmtToData.py to gather information from a run, or several runs, of the model.
# These produce allData.db files by default, though you can change that.  These files are the inputs
# to this program.
#
# Second, launch this program, e.g., py -3-64 frmtReport.py.
# The buttons at the top let you change the default input database (allData.db in the current directory
# by default) and output directory (current directory by default).  So, if you want, change them.
# Once you have selected a valid database a list of variables, with their associated subcategories,
# should display.
#
# Third, click on a variable name to get a resport.  This will generate one csv file for each subcategory.
#
# If you wish, you can click on other variables to get other reports, or select different input and output
# files and repeat.

from datetime import datetime
import os.path
import sys
import re
from PySide2 import QtCore, QtWidgets, QtGui, QtSql
from PySide2.QtSql import QSqlQuery
import pandas as pd
import numpy as np
from socket import getfqdn

class MyErr (Exception):
    pass

class MyWidget(QtWidgets.QWidget):
    def __init__(self, screenSize):
        super().__init__()

        self.text = QtWidgets.QLabel("CVD Model Result Disector")
        self.text.setAlignment(QtCore.Qt.AlignCenter)

        self.layout = QtWidgets.QVBoxLayout()

        self.layout.addWidget(self.text)

        self._initPaths()
    
        self._initVariables()

        # try to use the initial default database
        # This will populate the variable list if that works.
        # This may slow startup.
        self.getDatabase()
        self.vVariables.selectionModel().selectionChanged.connect(self.variableSelectionChanged)
        self.setLayout(self.layout)

    def getDatabase(self):
        """set database connection and cursor
        return True on success
        """
        # driver type is QtSql.QSqlDriver.SQLite
        if hasattr(self, "db"):
            self.db.close()
            del self.db
        self.db = QtSql.QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName(self.inName)
        success =  self.db.open()
        if success:
            self._linkVariables()
        else:
            del self.db
        return success

    def _initPaths(self):
        "GUI to set input and output paths"
        group = QtWidgets.QGroupBox()
        innerLayout = QtWidgets.QHBoxLayout()
        group.setLayout(innerLayout)
        self.vInName = QtWidgets.QPushButton("Input File")
        self.vOutDir = QtWidgets.QPushButton("Output Directory")
        innerLayout.addWidget(self.vInName)
        self.vInName.clicked.connect(self.inNameClicked)
        innerLayout.addWidget(self.vOutDir)
        self.vOutDir.clicked.connect(self.outDirClicked)
        self.layout.addWidget(group)
        self.inName = "allData.db"
        self.outDir = "."

    def inNameClicked(self):
        # getOpenFileName returns a tuple of fileName, selected filter
        self.inName = QtWidgets.QFileDialog.getOpenFileName(self, "Choose input database", os.path.dirname(self.inName), "SQLite Database (*.db)")[0]
        self.getDatabase()

    def outDirClicked(self):
        self.outDir = QtWidgets.QFileDialog.getExistingDirectory(self, "Output Directory for summary files", self.outDir)


    def _initVariables(self):
        "setup skeleton for view of variables in the database"
        self.vVariables = QtWidgets.QTableView()
        self.vVariables.resizeColumnsToContents()
        self.layout.addWidget(self.vVariables)

    def _linkVariables(self):
        "after a valid database connection is established should the variables in the associated widget"
        self.qVariables = QtSql.QSqlQueryModel()
        self.qVariables.setQuery("SELECT name, count(subCat) AS NSubGroups, group_concat(subcat, ' | ') as subGroups FROM "
                                    "fullvar LEFT OUTER JOIN variable USING (varid) "
                                    "GROUP BY varid ORDER BY name;")
        #self.qVariables.setQuery("SELECT name FROM variable ORDER BY name;")
        self.vVariables.setModel(self.qVariables)
        self.vVariables.resizeColumnsToContents()


    def variableSelectionChanged(self, selected, deselected):
        """User has selected a new variable.  For now just show most recent one.
        Write files to the output directory.
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
        for v in vars:
            self._doVar(v)

    def _doVar(self, v):
        "extract info for a single variable"
        q = QSqlQuery()
        q.prepare("SELECT fullvarid, subcat FROM fullvar INNER JOIN variable USING (varid) WHERE name = ?;")
        q.addBindValue(v)
        q.setForwardOnly(True)
        if not q.exec_():
             raise MyErr("Unable to get subcategories for {}: {}".format(v, q.lastError().text()))
        while q.next():
             self._doSubCat(q.value(0), v, q.value(1))

    def _doSubCat(self, fullvarid, var, subcat):
        """Output results for one particular var/subcat.
        This is the unit of the individual output file.
        fullvarid is the index of this particular var/subcat in the data
        var, subcat are the text names of same.

        There may be multiple scenarios within this category.
        Each gets a separate subtable.
        """
        f = self._openFile(var, subcat)
        q = QSqlQuery(("SELECT scenario, min(year) AS y0, max(year) AS y1 FROM data WHERE fullvarid = {}" +\
            " GROUP BY scenario ORDER BY scenario;").format(fullvarid))
        while q.next():
            f.write("Totals for {}-{}.\n".format(q.value(1), q.value(2)))
            self._doScenario(f, fullvarid, q.value(0))
        f.close()
        print("Done with {}: {}".format(var, subcat))

    def _openFile(self, var, subcat):
        "open an appropriately named file for var/subcat"
        if subcat == "-":
            name = var
        else:
            name = "{}_{}".format(var, subcat)
        name = re.sub("/", " or ", name)
        fname = "ageranges_{}.csv".format(name)
        fout = open(os.path.join(self.outDir, fname), "wt")
        if subcat == "-":
            fout.write(var)
        else:
            fout.write("{}: {}".format(var, subcat))
        fout.write(" Summary created by testqt.py run at {} on {} with results in file {}.\n".format(datetime.now(), getfqdn(), fname))
        return fout

    def _doScenario(self, fout, fullvarid, scenario):
        "Output appropriately rotated results for one scenario"
        QSqlQuery("DROP VIEW IF EXISTS allyrs;")
        groupVars = ["iSim", "label"]
        sqlGroups = ", ".join(groupVars)
        # parameters not allowed in views
        strSQL = "SELECT "+sqlGroups+", TOTAL(value) as v" +\
            " FROM data LEFT OUTER JOIN demo USING (demoid) " +\
            " WHERE fullvarid = {} AND scenario = '{}' GROUP BY ".format(fullvarid, scenario) +\
            sqlGroups +" ORDER BY "+ sqlGroups + ";"
        q = QSqlQuery()
        q.prepare("CREATE TEMP VIEW allyrs AS " + strSQL)
        if not q.exec_():
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
        colNames = ["file"] + labels
        self.df = pd.DataFrame(self._chunk(q, scenario, labels), columns=colNames)
        self._addTotals()
        self._addStats()
        # this option worked with to_string, but with to_csv it yields
        # TypeError: only size-1 arrays can be converted to Python scalars
        # float_format=(lambda a : np.format_float_positional(a, precision=2))
        self.df.to_csv(fout, line_terminator="\n")
        return self.df

    def _chunk(self, q, scenario, labels):
        """Rotate entries for one chunk and return a DataFrame.
        q is a query result with the necessary data, only for one fullvarid/scenario
        labels are the column labels
        a chunk is one particular variable, subCat, and scenario"""
        iSim = -1
        last_label = labels[len(labels)-1]
        while q.next():
            if iSim < 0:
                # start of this row
                t_row = [ scenario ]
            iSim = q.value(0)
            t_row.append(q.value(2))
            if q.value(1) == last_label:
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
        # the dtype of most columns, even the numbers, is object
        # so filtering based on dtype won't work
        aSumDF = self.df.iloc[:, 1:].describe(percentiles=(0.05, .10, .25, .5, .75, .9, .95))
        aSumDF.insert(0, "file", self.df.iloc[0, 0])
        self.df = pd.concat([aSumDF, self.df])
     
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
