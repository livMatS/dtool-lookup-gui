#
# Copyright 2021 Lars Pastewka
#           2021 Johannes Hörmann
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

from gi.repository import Gtk, Pango

DEFAULT_FORMATTER = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s: %(message)s')
SINGLE_MESSAGE_FORMATTER = logging.Formatter('%(levelname)s: %(message)s')

DEFAULT_TEXT_BUFFER_MAX_LINES = 1000
DEFAULT_ENTRY_MAX_LINES = 5
DEFAULT_LABEL_MAX_LINES = 1


# formatter mixins

class FormattedHandlerMixin():
    """Mixin for logging.Handler derivatives. Assigns formatter at creation."""
    def __init__(self, *args,
                 formatter: Optional[logging.Formatter] = DEFAULT_FORMATTER,
                 **kwargs):
        """Attach formatter to Handler instance."""
        super().__init__(*args, **kwargs)
        self.setFormatter(formatter)


class SingleMessageFormatHandlerMixin(FormattedHandlerMixin):
    """Mixin for logging.Handler derivatives. Assigns formatter at creation."""

    def __init__(self, *args,
                 formatter: Optional[logging.Formatter] = SINGLE_MESSAGE_FORMATTER,
                 **kwargs):
        """Attach formatter to Handler instance."""
        super().__init__(*args, formatter=formatter, **kwargs)


# handlers

class GtkBufferHandler(logging.Handler):
    def __init__(self, *args,
                 max_lines: Optional[int] = None,
                 **kwargs):
        """Abstract base class for any Gtk buffer handler.

        Limit maximum number of lines if max_lines set to int"""
        super().__init__(*args, **kwargs)
        self.max_lines = max_lines

    @property
    def max_lines(self, value: int):
        return self._max_lines

    @max_lines.setter
    def max_lines(self, value: Optional[int] = None):
        if value is None:
            self._max_lines = None # no limit
        elif isinstance(value, int) and value >= 0:
            self._max_lines = value
        else:
            raise ValueError(f"max_lines must be None or int, not {type(value)}.")

    def _insert_into_buffer(msg):
        ...

    def emit(self, record):
        """Emit log message to attached Gtk.TextBuffer."""
        try:
            msg = self.format(record)
            self._insert_into_buffer(msg)

        except Exception:
            self.handleError(record)


class GtkTextBufferHandler(GtkBufferHandler):
    def __init__(self, *args, text_buffer: Gtk.TextBuffer,
                 max_lines: Optional[int] = DEFAULT_TEXT_BUFFER_MAX_LINES,
                 **kwargs):
        """Tie a logging handler to a Gtk.TextBuffer.

        Limit maximum number of lines if max_lines set to int"""

        super().__init__(*args, max_lines=max_lines, **kwargs)
        self._buffer = text_buffer

        self._tag_bold = self._buffer.create_tag("bold", weight=Pango.Weight.BOLD)
        self._tag_italic = self._buffer.create_tag("italic", style=Pango.Style.ITALIC)


class GtkEntryBufferHandler(GtkBufferHandler):
    def __init__(self, *args, entry_buffer: Gtk.EntryBuffer,
                 max_lines: Optional[int] = DEFAULT_ENTRY_MAX_LINES, **kwargs):
        """Tie a logging handler to a Gtk.EntryBuffer.

        Limit maximum number of lines if max_lines set to int."""
        super().__init__(*args, max_lines=max_lines, **kwargs)
        self._buffer = entry_buffer


class GtkLabelHandler(GtkBufferHandler):
    def __init__(self, *args, label: Gtk.Label,
                 max_lines: Optional[int] = DEFAULT_LABEL_MAX_LINES, **kwargs):
        """Tie a logging handler to a Gtk.EntryBuffer.

        Limit maximum number of lines if max_lines set to int."""
        super().__init__(*args, max_lines=max_lines, **kwargs)
        self._buffer = label


class AppendingGtkTextBufferHandler(GtkTextBufferHandler):
    def _insert_into_buffer(self, msg):
        """Appends log message to attached Gtk.TextBuffer."""

        # remove all tags from buffer
        start_iter = self._buffer.get_start_iter()
        end_iter = self._buffer.get_end_iter()
        self._buffer.remove_tag(self._tag_bold, start_iter, end_iter)

        # insert new message at end
        self._buffer.insert_with_tags(end_iter, msg + "\n", self._tag_bold)

        # crop lines at end of buffer
        if (self._max_lines is not None
                and self._buffer.get_line_count() > self._max_lines):
            lines_to_remove = self._buffer.get_line_count() - self._max_lines
            start_iter = self._buffer.get_start_iter()
            end_iter = self._buffer.get_iter_at_line(lines_to_remove)
            self._buffer.delete(start_iter, end_iter)

        # place cursor at end
        self._buffer.place_cursor(self._buffer.get_end_iter())


class PrependingGtkTextBufferHandler(GtkTextBufferHandler):
    def _insert_into_buffer(self, msg):
        """Prepends log message to attached Gtk.TextBuffer."""

        # remove all tags from buffer
        start_iter = self._buffer.get_start_iter()
        end_iter = self._buffer.get_end_iter()
        self._buffer.remove_tag(self._tag_bold, start_iter, end_iter)

        # insert new message at beginning
        self._buffer.insert_with_tags(start_iter, msg + "\n", self._tag_bold)

        # crop lines at end of buffer
        if (self._max_lines is not None
                and self._buffer.get_line_count() > self._max_lines):
            lines_to_remove = self._buffer.get_line_count() - self._max_lines
            end_iter = self._buffer.get_end_iter()
            start_iter = self._buffer.get_iter_at_line(self._max_lines-lines_to_remove)
            self._buffer.delete(start_iter, end_iter)

        # place cursor at beginning
        self._buffer.place_cursor(self._buffer.get_start_iter())


class AppendingGtkEntryBufferHandler(GtkEntryBufferHandler):
    def _insert_into_buffer(self, msg):
        """Appends log message to attached Gtk.Entry."""

        # shorten message if too long
        if len(msg.splitlines()) > self._max_lines:
            new_text = "\n".join([
                *msg.splitlines()[:self._max_lines//2],
                '...'
                * msg.splitlines()[self._max_lines//2+1:]
            ])
        else: # crop older messages if too long
            original_text = self._buffer.get_text()
            new_text = original_text + "\n" + msg
            if (self._max_lines is not None
                    and len(new_text.splitlines()) > self._max_lines):
                lines_to_remove = len(new_text.splitlines()) - self._max_lines
                new_text = "\n".joint(new_text.splitlines()[lines_to_remove:])

        self._buffer.set_text(new_text)


class SingleMessageGtkEntryBufferHandler(GtkEntryBufferHandler):
    def _insert_into_buffer(self, msg):
        """Store log message in Gtk.Entry."""

        # shorten message if too long
        if len(msg.splitlines()) > self._max_lines:
            new_text = "\n".join([
                *msg.splitlines()[:self._max_lines//2],
                '...'
                * msg.splitlines()[self._max_lines//2+1:]
            ])
        else:
            new_text = msg
        self._buffer.set_text(new_text)


class SingleMessageGtkLabelHandler(GtkLabelHandler):
    """Show last line of log message on Gtk.Label."""
    def _insert_into_buffer(self, msg):
        """Store log message in Gtk.Label."""

        # shorten message if too long
        if len(msg.splitlines()) > self._max_lines:
            new_text = "\n".join(msg.splitlines()[-self._max_lines:])
        else:
            new_text = msg
        self._buffer.set_text(new_text)


class SingleMessageGtkInfoBarHandler(SingleMessageGtkLabelHandler):
    """Reveal attached Gtk.InfoBar when logging."""
    def __init__(self, *args, info_bar: Gtk.InfoBar, **kwargs):
        super().__init__(*args, **kwargs)
        self._info_bar = info_bar

    def emit(self, record):
        super().emit(record)
        self._info_bar.show()
        self._info_bar.set_revealed(True)


class FormattedAppendingGtkTextBufferHandler(FormattedHandlerMixin, AppendingGtkTextBufferHandler):
    pass


class FormattedPrependingGtkTextBufferHandler(FormattedHandlerMixin, PrependingGtkTextBufferHandler):
    pass


class FormattedSingleMessageGtkLabelHandler(SingleMessageFormatHandlerMixin, SingleMessageGtkLabelHandler):
    pass


class FormattedSingleMessageGtkInfoBarHandler(SingleMessageFormatHandlerMixin, SingleMessageGtkInfoBarHandler):
    pass
