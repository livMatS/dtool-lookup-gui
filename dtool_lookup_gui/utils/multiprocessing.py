#
# Copyright 2021 Johanns Hoermann
#
# ### MIT license
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
"""Multiprocessing utils."""

# NOTE: depending on platform, we may have to experiment with the forking methods,
# https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods

import logging
import multiprocessing  # run task as child process to avoid side effects
import queue
import traceback  # forward exception from child process to parent process


logger = logging.getLogger(__name__)


# inspired by
# https://stackoverflow.com/questions/19924104/python-multiprocessing-handling-child-errors-in-parent
class Process(multiprocessing.Process):
    """
    Class which returns child Exceptions to Parent.
    https://stackoverflow.com/a/33599967/4992248
    """

    def __init__(self, *args, **kwargs):
        multiprocessing.Process.__init__(self, *args, **kwargs)
        self._parent_conn, self._child_conn = multiprocessing.Pipe()
        self._exception = None

    def run(self):
        try:
            super().run()
            self._child_conn.send(None)
        except Exception as e:
            tb = traceback.format_exc()
            self._child_conn.send((e, tb))
            raise e  # You can still rise this exception if you need to

    @property
    def exception(self):
        if self._parent_conn.poll():
            self._exception = self._parent_conn.recv()
        return self._exception


class StatusReportingChildProcessBuilder:
    """Outsource serial functions with status report handlers.

    The status report handler is expected to conform to the
    click.ProgressBar interface. In particular, it must exhibit an
    update(val) method.

    For any function that runs serial and reports status via such a callback,
    this wrapper can run them in a non-blocking forked process and forward the
    status reports via queue to the callback.

    The function must have the signature

        func(*args, status_report_callback=None, stop_event_callback=None)

    and need not make use of any of the two callback functions. It can check on
    the stop_event_callback() to finish gracefully when the parent process wants
    the child process to finish.
    """
    def __init__(self, target, status_report_callback):
        self._target = target
        self._status_report_handler = status_report_callback

    def __call__(self, *args):
        """Spawn child process to assure my environment stays untouched."""
        return_value_queue = multiprocessing.Queue()
        status_progress_queue = multiprocessing.Queue()
        stop_event = multiprocessing.Event()
        process = Process(target=self.target_wrapper, args=[return_value_queue, status_progress_queue, stop_event, *args])
        process.start()

        # wait for child to queue objects and
        # check whether child raises exception
        while return_value_queue.empty():
            # if child raises exception, then it has terminated
            # before queueing any fw_action object
            if process.exception:
                error, p_traceback = process.exception
                raise ChildProcessError(p_traceback)

            try:
                status_report = status_progress_queue.get_nowait()
            except queue.Empty:
                pass
            else:
                logger.debug(f"Parent process received status report {status_report}")
                self._status_report_handler.update(status_report)

            # let child process stop
            if hasattr(self, '_stop_event') and hasattr(self._stop_event, 'is_set'):
                if self._stop_event.is_set():
                    stop_event.set()

        # this loop will deadlock for any child that never raises
        # an exception and does not queue anything

        # queue only used for one transfer of
        # return fw_action, should thus never deadlock.
        return_value = return_value_queue.get()
        # if we reach this line without the child
        # queueing anything, then process will deadlock.
        process.join()
        return return_value

    def target_wrapper(self, return_value_queue, status_progress_queue, stop_event, *args):

        class StatusReportClass:
            def update(status_report):
                logger.debug(f"Child process queues status report {status_report}")
                status_progress_queue.put(status_report)

        def stop_event_callback():
            logger.debug(f"Child process checks stop event.")
            return stop_event.is_set()

        return_value_queue.put(self._target(*args, status_report_callback=StatusReportClass, stop_event_callback=stop_event_callback))

    def set_stop_event(self, e):
        """This can be a threaded event and will be forwarded to the child process."""
        self._stop_event = e


def test_function(steps, status_report_callback, stop_event_callback=None):
    for n in range(steps):
        print(f"Child process step {n}")
        status_report_callback.update(n)
        if stop_event_callback is not None and stop_event_callback():
            return False

    return True


class test_handler:
    def update(n):
        print(f"Test callback received report for step {n}")


def test_run():
    test_process = StatusReportingChildProcessBuilder(test_function, test_handler)
    return_value = test_process(10)
    print(f"Child process returned {return_value}.")
