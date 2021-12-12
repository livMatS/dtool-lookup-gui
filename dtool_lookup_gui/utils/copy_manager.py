#
# Copyright 2021 Lars Pastewka
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

class CopyManager:
    """Keep track of running copy operations"""

    _margin = 6

    def __init__(self, progress_revealer, progress_popover):
        # Note: This is not particularly abstract, as it interacts directly with the Gtk widgets
        self._progress_revealer = progress_revealer
        self._progress_chart = progress_revealer.get_child().get_child()
        self._progress_popover = progress_popover

    async def copy(self, dataset, destination):
        self._progress_revealer.set_reveal_child(True)
        tracker = self._progress_popover.add_status_box(
            self.progress_update, f'Copying dataset »{dataset}« to »{destination}«')
        await dataset.copy(destination, progressbar=tracker)
        tracker.set_done()

        # Once all copy operations are done, we hide the pie chart and clear the popover
        if all([tracker.is_done for tracker in self._progress_popover.status_boxes]):
            for tracker in self._progress_popover.status_boxes:
                tracker.destroy()
            self._progress_revealer.set_reveal_child(False)

    def progress_update(self):
        # Refresh pie chart
        total_length = sum([len(tracker) for tracker in self._progress_popover.status_boxes])
        total_step = sum([tracker.step for tracker in self._progress_popover.status_boxes])
        self._progress_chart.set_fraction(total_step / total_length)
