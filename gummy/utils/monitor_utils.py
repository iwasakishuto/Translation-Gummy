# coding: utf-8
import sys
import time

from .coloring_utils import toACCENT, toBLUE

class ProgressMonitor():
    """
    Monitor the loop progress.
    @params max_iter: (int) Maximum number of iterations.
    @params verbose : (int) -1, 0, 1
        -1 = silent
        0  = only progress bar
        1  = progress bar and metrics
    @params barname : (str)
    ~~~
    examples)
    >>> from kerasy.utils import ProgressMonitor
    >>> max_iter = 100
    >>> monitor = ProgressMonitor(max_iter=max_iter, verbose=1, barname="NAME")
    >>> for it in range(max_iter):
    >>>     monitor.report(it, loop=it)
    >>> monitor.remove()
    NAME 100/100[####################]100.00% - 0.010[s]  loop: 99
    """
    def __init__(self, max_iter, verbose=1, barname="", **kwargs):
        self._reset()
        self.max_iter = max_iter
        self.digit = len(str(max_iter))
        self.verbose = verbose
        self.barname = barname + " " if len(barname)>0 else ""
        self.report = {
            -1 : self._report_silent,
             0 : self._report_only_prograss_bar,
             1 : self._report_progress_bar_and_metrics,
        }.get(verbose, self._report_progress_bar_and_metrics)
        self.report(it=-1)

    def _reset(self):
        self.histories = {}
        self.iter = 0
        self.initial_seconds_since_epoch = time.time()

    def _report_silent(self, it, **metrics):
        pass

    def _report_only_prograss_bar(self, it, **metrics):
        it += 1
        sys.stdout.write(
            f"\r{self.barname}{it:>0{self.digit}}/{self.max_iter} " + \
            f"[{('#' * int((it/self.max_iter)/0.05)).ljust(20, '-')}]" + \
            f"{it/self.max_iter:>7.2%} - {time.time()-self.initial_seconds_since_epoch:.3f}[s]"
        )

    def _report_progress_bar_and_metrics(self, it, **metrics):
        it += 1
        metric = ", ".join([f"{toACCENT(k)}: {toBLUE(v)}" for  k,v in metrics.items()])
        sys.stdout.write(
            f"\r{self.barname}{it:>0{self.digit}}/{self.max_iter}" + \
            f"[{('#' * int((it/self.max_iter)/0.05)).ljust(20, '-')}]" + \
            f"{it/self.max_iter:>7.2%} - {time.time()-self.initial_seconds_since_epoch:.3f}[s]   " + \
            f"{metric}"
        )

    def remove(self):
        def _pass():
            pass
        {
            -1: _pass,
             0: print,
             1: print,
        }.get(self.verbose, print)()