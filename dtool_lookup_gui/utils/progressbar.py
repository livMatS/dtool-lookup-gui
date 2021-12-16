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

"""Progressbar"""

import logging

from gi.repository import Gtk

from contextlib import AbstractContextManager
from typing import Optional

logger = logging.getLogger(__name__)


class ProgressBar(AbstractContextManager):
    """Mimics click.progressbar". Just log messages if no progressbar specified."""
    def __init__(self, length=None, label=None,
                 pb: Optional[Gtk.ProgressBar] = None):
        # if pb is None:
        #    pb = Gtk.ProgressBar(show_text=True, text=None)
        self._pb = pb
        self._item_show_func = None
        self._label_template = '{label:}'
        self._label_item_template = '{label:} ({item:})'
        self._label = label
        self._length = length
        self._step = 0

    def __enter__(self):
        if self._pb is not None:
            if hasattr(self._pb, 'set_fraction'):
                self._pb.set_fraction(0.0)
            if hasattr(self._pb, 'set_step'):
                self._pb.set_step(0, self._length)
        logger.info(f"Progress fraction 0.0")
        self._set_text()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, label):
        self._label = label
        self._set_text()

    @property
    def item_show_func(self):
        return self._item_show_func

    @item_show_func.setter
    def item_show_func(self, item_show_func):
        self._item_show_func = item_show_func
        self._set_text()

    def update(self, step):
        self._step += step
        fraction = float(self._step) / float(self._length)
        if self._pb is not None:
            if hasattr(self._pb, 'set_fraction'):
                self._pb.set_fraction(fraction)
            if hasattr(self._pb, 'set_step'):
                self._pb.set_step(self._step, self._length)
        logger.info(f"Progress fraction {fraction}")
        self._set_text()

    def _set_text(self):
        if self._label is not None and self._item_show_func is not None:
            text = self._label_item_template.format(
                label=self._label, item=self.item_show_func(self._step))
            if self._pb is not None:
                self._pb.set_text(text)
        if self._label is not None:
            text = self._label_template.format(label=self._label)
            if self._pb is not None:
                self._pb.set_text(text)
        else:
            text = None
            if self._pb is not None:
                self._pb.set_show_text(False)

        if text is not None:
            logger.info(text)