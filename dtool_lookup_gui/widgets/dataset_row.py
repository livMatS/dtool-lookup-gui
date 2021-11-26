#
# Copyright 2021 Lars Pastewka, Johanns Hoermann
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

import locale
from contextlib import contextmanager
from datetime import date, datetime

from gi.repository import Gtk

import dtoolcore.utils


@contextmanager
def time_locale(name):
    # This code snippet was taken from:
    # https://stackoverflow.com/questions/18593661/how-do-i-strftime-a-date-object-in-a-different-locale
    saved = locale.setlocale(locale.LC_TIME)
    try:
        yield locale.setlocale(locale.LC_TIME, name)
    finally:
        locale.setlocale(locale.LC_TIME, saved)


def to_timestamp(d):
    """
    Convert a string or a timestamp to a timestamp. This is a dirty fix necessary
    because the /dataset/list route return timestamps but /dataset/search
    returns strings in older versions of the lookup server (before 0.15.0).
    """
    if type(d) is str:
        try:
            with time_locale('C'):
                d = dtoolcore.utils.timestamp(datetime.strptime(d, '%a, %d %b %Y %H:%M:%S %Z'))
        except ValueError as e:
            d = -1
    return d


def date_to_string(d):
    return date.fromtimestamp(to_timestamp(d))


class DtoolDatasetRow(Gtk.ListBoxRow):
    __gtype_name__ = 'DtoolDatasetRow'

    _margin = 3

    def __init__(self, dataset, *args, **kwargs):
        self.dataset = dataset

        super().__init__(*args, **kwargs)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_top=self._margin, margin_bottom=self._margin,
                       margin_start=self._margin, margin_end=self._margin)
        label = Gtk.Label(xalign=0)
        label.set_markup(f'<b>{dataset.uuid}</b>')
        vbox.pack_start(label, True, True, 0)
        label = Gtk.Label(xalign=0)
        label.set_markup(f'{dataset.name}')
        vbox.pack_start(label, True, True, 0)
        label = Gtk.Label(xalign=0)
        label.set_markup(
            f'<small>Created by: {dataset.creator}, '
            f'frozen at: '
            f'{date_to_string(dataset.date)}</small>')
        vbox.pack_start(label, True, True, 0)
        self.add(vbox)
