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


@Gtk.Template(filename=f'{os.path.dirname(__file__)}/authentication_dialog.ui')
class AuthenticationDialog(Gtk.Window):
    __gtype_name__ = 'DtoolAuthenticationDialog'

    username_entry = Gtk.Template.Child()
    password_entry = Gtk.Template.Child()

    def __init__(self, apply=lambda username, password: None, username=None, password=None, **kwargs):
        super().__init__(**kwargs)
        if username:
            self.username_entry.set_text(username)
        if password:
            self.password_entry.set_text(password)
        self._apply = apply

    @Gtk.Template.Callback()
    def on_apply_clicked(self, widget):
        self._apply(self.username_entry.get_text(), self.password_entry.get_text())
        self.destroy()

    @Gtk.Template.Callback()
    def on_cancel_clicked(self, widget):
        self.destroy()
