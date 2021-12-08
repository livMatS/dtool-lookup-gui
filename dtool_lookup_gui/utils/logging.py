#
# Copyright 2021 Johannes Hoermann, Lars Pastewka
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
import logging
from typing import Optional

from gi.repository import Gtk

default_formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')


class FormattedHandlerMixin():
    def __init__(self, *args,
                 formatter: Optional[logging.Formatter] = default_formatter,
                 **kwargs):
        """Attach formatter to all handlers."""
        super().__init__(*args, **kwargs)
        self.setFormatter(formatter)


class GtkTextBufferHandler(logging.Handler):
    def __init__(self, *args, text_buffer: Gtk.TextBuffer,
                 max_lines: Optional[int] = 30, **kwargs):
        """Tie a logging handler to a Gtk.TextBuffer.

        Limit maximum number of lines if max_lines set to int"""

        super().__init__(*args, **kwargs)
        self._buffer = text_buffer
        self._max_lines = max_lines

    def emit(self, record):
        try:
            msg = self.format(record)

            end_iter = self._buffer.get_end_iter()
            self._buffer.insert(end_iter, msg + "\n")
            if (self._max_lines is not None
                    and self._buffer.get_line_count() > self._max_lines):
                lines_to_remove = self._buffer.get_line_count() - self._max_lines
                start_iter = self._buffer.get_start_iter()
                end_iter = self._buffer.get_iter_at_line(lines_to_remove)
                self._buffer.delete(start_iter, end_iter)
        except Exception:
            self.handleError(record)


class GtkEntryBufferHandler(logging.Handler):
    def __init__(self, *args, entry_buffer: Gtk.EntryBuffer,
                 max_lines: Optional[int] = None, **kwargs):
        """Tie a logging handler to a Gtk.EntryBuffer.

        Limit maximum number of lines if max_lines set to int."""
        super().__init__(*args, **kwargs)
        self._buffer = entry_buffer
        self._max_lines = max_lines

    def emit(self, record):
        try:
            msg = self.format(record)

            original_text = self._buffer.get_text()
            new_text = original_text + "\n" + msg
            if (self._max_lines is not None
                    and len(new_text.splitlines()) > self._max_lines):
                lines_to_remove = len(new_text.splitlines()) - self._max_lines
                new_text = "\n".joint(new_text.splitlines()[lines_to_remove:])

            self._buffer.set_text(new_text)
        except Exception:
            self.handleError(record)


class FormattedGtkTextBufferHandler(FormattedHandlerMixin, GtkTextBufferHandler):
    pass


class FormattedGtkEntryBufferHandler(FormattedHandlerMixin, GtkTextBufferHandler):
    pass
