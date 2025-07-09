"""Each class here takes a call with a message from SwitchBoard
and does something useful with the message.

All must be callable with 2 arguments, a json object and its
string representation.  They must *not* modify either.

They should also implement a close() method to do whatever cleanup is
necessary.
"""
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

class StupidLogfile:
    "really simple logging to a file"
    def __init__(self, logfile: Path|str):
        self._logfile = Path(logfile)
        self._fout = self._logfile.open("at")

    def __call__(self, obj, json_str):
        "log the message"
        self._fout.write(json_str+"\n")

    def close(self):
        self._fout.close()

class DumbTerminalLog:
    """simple logging that works for any stdout
    No coloring, beeping or styling.
    No curses-type manipulation.
    No filtering out unimportant info.
    """
    def __call__(self, obj, json_str):
        print(json_str)

    def close(self):
        "Leave it open for others"
        pass

class TimerLog:
    """Collect timing info about individual iterations, all runs.
    Also prints error messages.
    """
    def __init__(self, niter: int, nrun: int):
        """there will be niter iterations for each of nrun parallel runs
        Stores time as  floating point seconds, although time inputs are
        integer milliseconds.  The change is mostly motivated by the
        absence of an integral NaN value in numpy; it is also slightly easier 
        to interpret.

        The numpy documentation recommends against, and declares obsolete,
        masked arrays in the numpy.ma module.  They are another way to handle missings.

        numpy has a native type datetime64 with a missing value NaT (not a time).
        This propagates properly in arithmetic operations, but is not integrated 
        with the nan* functions.  So it is not a convenient alternative.
        """

        self._start = np.full((niter, nrun), np.nan)
        self._end = self._start.copy()
        self._delta = self._start.copy() # delta[i, r] = end[i, r] - start[i, r]
        self._gap = self._start.copy() # gap[i, r] = start[i+1, r] - end[i, r]
        self._niter = niter
        self._nrun = nrun

    def __call__(self, obj, json_str):
        # use get in case there is no key
        # in which case result is None
        iter = obj.get("iteration")
        run = obj.get("runid")
        if obj["type"] == "PROGRESS":
            s = obj.get("endTime")
            if s:
                self.setEnd(iter, run, s)
                # we should already have the start time
            else:
                s = obj.get("startTime")
                if s:
                    self.setStart(iter, run, s)
        elif obj["type"] == "ERR":
            print(json_str)
        # otherwise do nothing

    def setStart(self, iter: int, run: int, milli: int):
        "note that iteration iter of run run started at milli milliseconds since the epoch"
        s = milli/1000  # always a float, even if 1000/1000
        irun = run - 1
        self._start[iter, irun] = s
        if iter>0:
            self._gap[iter-1, irun] = s - self._end[iter-1, irun]
            self.updateGap(iter-1, run)

    def setEnd(self, iter: int, run: int, milli: int):
        "note that iteration iter of run run ended at milli milliseconds since the epoch"
        s = milli/1000
        irun = run - 1
        self._end[iter, irun] = s
        self._delta[iter, irun] = s - self._start[iter, irun]
        self.updateDelta(iter, run)

    def delta(self):
        """Return entire delta matrix of end-start
        """
        return self._delta
    
    def gap(self):
        "return entire gap matrix of start[i+1]-end[i]"
        return self._gap
    
    def updateDelta(self, iter, run):
        "tell those interested a delta value changed"
        pass

    def updateGap(self, iter, run):
        "tell those interested a gap value changed"
        pass

    def meanTimes(self):
        """Compute average time per iteration by run.
        I could just get last-first, but that  won't work
        for more irregular patterns.
        May return nan values.
        """
        return np.nanmean(self._delta + self._gap, axis=0)
    
    def meanDelta(self):
        "average iteration run time by run"
        return np.nanmean(self._delta)
    
    def meanGap(self):
        "average time between end of one iteration and start of next, by run"
        return np.nanmean(self._gap, axis=0)

    def iterRemaining(self):
        """ Remaining iterations, by run
        """
        # np.count_nonzero works, but if any time happens to be 0 it won't
        return np.sum(np.isnan(self._end), axis=0)
    
    def timeRemaining(self):
        """how many seconds til all iterations for are done. by run
        Since the calculations are not atomic they might be subject to
        a race, but single-threaded async code should be safe.
        """
        return self.meanTimes()*self.iterRemaining()

class TerminalTimerLog(TimerLog):
    """Simple progress reports to dumb terminal
    Issues updated summary reports periodically via the async call monitor().
    """
    def __init__(self, iter: int, nrun: int, updateInterval=timedelta(minutes=5)):
        "Print a summary report every updateInterval"
        super().__init__(iter, nrun)
        self._dirty = False   # has anything changed since last report?
        self._onedone = False  # has at least one job finished?  Otherwise no stats.
        self._delay = updateInterval.total_seconds()

    DAY = timedelta(days=1)
    HOUR = timedelta(hours=1)
    MINUTE = timedelta(minutes=1)

    def format_delta(self, delta: float|timedelta)->str:
        """convert a single time duration in seconds into d:h:m, omitting parts that are 0
        delta may also be np.nan -> ?
        """
        # check for nan first to avoid an error if try to construct timedelta with it
        if np.nan == delta:
            return "?"
        if not isinstance(delta, timedelta):
            delta = timedelta(seconds=delta)
        d = delta.days
        if d:
            if d == 1:
                r = "1 day "
            else:
                r = f"{d} days "
            delta %= self.DAY
        else:
            r = ""
        h = delta//self.HOUR
        if h:
            r += f"{h}h "
            delta %= self.HOUR
        m = delta / self.MINUTE
        r += f"{m:4.1f}m"
        return r


    def report(self):
        "print a short summary"
        if  not (self._dirty and self._onedone):
            return
        self._dirty = False
        remain = self.timeRemaining()
        worst = timedelta(seconds=np.nanmax(remain))
        ntogo = self.iterRemaining()
        atleast_one = np.all(ntogo < self._niter)
        now = datetime.now()
        eta = now+worst
        if not atleast_one:
            print("WARNING: Some runs have yet to complete their first iteration. ETA likely too soon.")
        remainings = ", ".join(self.format_delta(x) for x in remain)
        print(f"ETA {eta:%a %b %d %H:%M} ({self.format_delta(worst)} from now).  iter left: {ntogo}")
        print(f"  time left: {remainings} as of {datetime.now():%a %b %d %H:%M:%S}")

    async def monitor(self):
        while not np.all(self.iterRemaining() == 0):
            await asyncio.sleep(self._delay)
            self.report()

    def setStart(self, iter: int, run: int, milli: int):
        "note that iteration iter of run run started at milli milliseconds since the epoch"
        self._dirty = True
        super().setStart(iter, run, milli)


    def setEnd(self, iter: int, run: int, milli: int):
        "note that iteration iter of run run ended at milli milliseconds since the epoch"
        self._dirty = True
        self._onedone = True
        super().setEnd(iter, run, milli)