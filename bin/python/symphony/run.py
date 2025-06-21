import asyncio
from datetime import datetime, timedelta
import json
from pathlib import Path
import re

class AbstractRun:
    """Describes and manages a single `mc run` invocation.
    A run may cover one more scenarios (`.inp` files) and may 
    cover all or some of the iterations of interest.
    A run takes place in a single directory, which takes
    the role of root of the data directories for a project.

    Subclasses must implement the following methods
    root()->Path the top level directory from which the simulations run
    name()->str  a human-friendly name for the run, usual same as last 
                  component of root
    lasti()->int  last iteration number completed
    startTime()->DateTime or None.  When this whole run began.
    lastiTime()->DateTime or None. When iteration lasti finished.
    averageTime()->timedelta Average time for one iteration.
    longestTime()->timedelta longest time for one iteration
    shortestTime()->timedelta shortest time for one iteration
    The timing information should exclude iteration 0 if possible,
    since it involves less processing.
    remainingIterations()  number iterations left
    completeIterations() number of iterations completed
    averageTimeRemaining() timedelta until completion
    optimisticTimeRemaining()
    pessimisticTimeRemaining()
    completionTime() DateTime estimated based on averageTime
    optimisticCompletionTime() DateTime
    pessimisticCompletionTime() DateTime

    The system hits patches of extreme slowness, and so the length
    of time an iteration takes is expected to vary.  The remaining
    iterations may occur during an unusually slow or fast period;
    the optimistic estimates assume remining iterations will be fast,
    and the pessimistic ones assume it will be slow.

    """
    _instances = {}  # keys are ids, values are instances of AbstractRun subclasses

    @staticmethod
    def _newrun(aRun: "AbstractRun")->int:
        "register a new run object, returning and setting its id"
        i = len(AbstractRun._instances)+1
        aRun._id = i
        AbstractRun._instances[i] = aRun
        return i
    
    def __init__(self):
        self._newrun(self)

class SingleScenarioRun(AbstractRun):
    """Does a complete run of a single .inp scenario.

    Currently runs with --overwrite, a dangerous option.
    This is to permit repeated testing.
    """
    def __init__(self, basics: "Basics", scenario: str, iterations=1001, seed=345):
        super().__init__()
        self._root = basics.pdir / scenario
        self._scenario = scenario
        self._cmd = [basics.MYNODE, basics.MYMC, "run", str(iterations), "0", str(seed),
                     "--json", "--overwrite", "--python", basics.MYPY]
        self._niter = iterations
        self._lasti = -1
        self._startTime = None
        self._status = "starting"

    NOT_ERR_RE = re.compile("^((Debugger (listening on|attached))|For help, see|Waiting for the debugger)", re.I)

    def root(self):
        "top directory for data files. Will be working directory for programs."
        return self._root
    
    def name(self)->str:
        "friendly name for self"
        return self._scenario
    
    def lasti(self)->int:
        """last iteration completed.
        This is the index number of the iteration; if a run is iterations
        500-600 and 501 is the last one completed, this function returns 501,
        not 1 or 2.
        <0 means nothing done
        """
        return self._lasti
    
    def remainingIterations(self)->int:
        "Number of iterations still to go"
        # this logic would not work for partial runs
        return self._niter - self._lasti-1
    
    def completeIterations(self)->int:
        "Iterations done, remembering we start at 0"
        return 1+self._lasti
    
    async def run(self, switchboard)->int|None:
        """Run the job, reporting results to switchboard in real time.
        """
        self._status = "running"
        p = await asyncio.create_subprocess_exec(*self._cmd, 
                                                 cwd=self.root(),
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.PIPE)
        taskout = None
        taskerr = None
        while not (p.stdout.at_eof() and p.stderr.at_eof()):
            if taskout is None:
                taskout = asyncio.create_task(p.stdout.readline(), name="stdout")
            if taskerr is None:
                taskerr = asyncio.create_task(p.stderr.readline(), name="stderr")
            done, pending = await asyncio.wait(
                [taskout, taskerr],
                return_when=asyncio.FIRST_COMPLETED)
            for s in done:
                line = s.result()
                # I generally get back 0 byte string for stderr even when nothing was written to stderr
                n = len(line)
                if n:
                    line = line.decode().rstrip()
                if s.get_name() == "stderr":
                    taskerr = None
                    if n:
                        # everything to stderr is plain text
                        # make fake JSON object
                        if self.NOT_ERR_RE.match(line):
                            this_type = "INFO"
                        else:
                            this_type = "ERR"
                        m = {"type": this_type, "text": line,
                             "runid": self._id, "lasti": self._lasti}
                        if this_type == "ERR":
                            self._failed(m)
                        await switchboard.message_obj(m)

                else:
                    taskout = None
                    if n:
                        try:
                            data = json.loads(line)
                            if data["type"] == "ERR":
                                self._failed(data)
                            data["runid"] = self._id
                            data["lasti"] = self._lasti
                            self._special_handling(data)
                        except json.decoder.JSONDecodeError:
                            data = line.rstrip()
                            data = {"type": "stdout", "text": data,
                                    "runid": self._id, "lasti": self._lasti}
                        await switchboard.message_obj(data)
                            

        if self._status != "error":
            self._status = "done"
        return p.returncode

    def _failed(self, obj):
        """Note failure with associated JSON object
        Should I abort here?"""
        self._status = "error"
        self._status_info = obj

    def _special_handling(self, obj):
        """
        Check obj, an object representing a JSON message,
        for any special processing.  May modify obj.
        """
        if obj["type"] == "PROGRESS":
            # TO DO record progress in matrix

            # strings that are integers are already converted to in
            # for a in ("remaining", "iteration"):
            #     obj[a] = int(obj[a])
            for a in ("startTime", "endTime"):
                obj[a] = datetime.fromtimestamp(obj[a]/1000)
            a = "lastTime"
            obj[a] = timedelta(milliseconds=obj[a])
            self._lasti = obj["iteration"]

