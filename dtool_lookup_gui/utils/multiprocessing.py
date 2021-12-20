#
# Copyright 2021 Johannes Hörmann
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

import asyncio
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

        func(*args, status_report_callback=None)
    """
    def __init__(self, target, status_report_callback):
        self._target = target
        self._status_report_handler = status_report_callback

    async def __call__(self, *args):
        """Spawn child process to assure my environment stays untouched."""
        return_value_queue = multiprocessing.Queue()
        status_progress_queue = multiprocessing.Queue()
        process = Process(target=self.target_wrapper, args=[return_value_queue, status_progress_queue, *args])
        process.start()

        # wait for child to queue its return value and
        # check whether child raises exception
        while return_value_queue.empty():
            # if child raises exception, then it has terminated
            # before queueing any return value
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

            await asyncio.sleep(0.1)

        return_value = return_value_queue.get()
        # for any child that never raises an exception and does not queue
        # anything to the return_value_queue, will deadlock here
        process.join()
        return return_value

    def target_wrapper(self, return_value_queue, status_progress_queue, *args):

        class StatusReportClass:
            def update(status_report):
                logger.debug(f"Child process queues status report {status_report}")
                status_progress_queue.put(status_report)

        return_value_queue.put(self._target(*args, status_report_callback=StatusReportClass))


def test_function(steps, status_report_callback):
    for n in range(steps):
        print(f"Child process step {n}")
        status_report_callback.update(n)

    return True


class test_handler:
    def update(n):
        print(f"Test callback received report for step {n}")


async def test_run():
    test_process = StatusReportingChildProcessBuilder(test_function, test_handler)
    return_value = await test_process(10)
    print(f"Child process returned {return_value}.")
