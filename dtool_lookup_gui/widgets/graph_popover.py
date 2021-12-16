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

import os

from gi.repository import Gtk


@Gtk.Template(filename=f'{os.path.dirname(__file__)}/graph_popover.ui')
class DtoolGraphPopover(Gtk.Popover):
    __gtype_name__ = 'DtoolGraphPopover'

    uuid_label = Gtk.Template.Child()
    name_label = Gtk.Template.Child()
    show_dataset_button = Gtk.Template.Child()

    def __init__(self, *args, **kwargs):
        on_show_clicked = kwargs.pop('on_show_clicked', None)
        super().__init__(*args, **kwargs)
        if on_show_clicked is not None:
            self.show_dataset_button.connect('clicked', on_show_clicked)

    @property
    def uuid(self):
        self.uuid_label.get_text()

    @uuid.setter
    def uuid(self, uuid):
        self.uuid_label.set_text(uuid)

    @property
    def name(self):
        self.name_label.get_text()

    @uuid.setter
    def name(self, name):
        self.name_label.set_text(name)
