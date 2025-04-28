<#
**This MUST be run by using `. my.ps1` or to work.**
It activates the python virtual environment and sets the PowerShell variables $MYMC and $MYPY so that they will work from anywhere, including
the data directory for a project.

So typical use of those variables would be
```ps1
node $MYMC init
node $MYMC run 0 1000 345 --python $MYPY
```
This all assumes you are using PowerShell.
#>
$thisDir = $PSScriptRoot  # the location of this source file, regardless of where it is run from
$MYPY = Join-Path $thisDir "pyenv\Scripts\python.exe" -Resolve # the python executable in the virtual environment
$MYMC = Join-Path $thisDir "bin\mc.js" -Resolve

# finally, activate the venv
. (Join-Path $thisDir "pyenv\Scripts\Activate.ps1")
