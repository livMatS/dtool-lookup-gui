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

from dtoolcore.utils import NAME_VALID_CHARS_LIST, name_is_valid


@Gtk.Template(filename=f'{os.path.dirname(__file__)}/dataset_name_dialog.ui')
class DatasetNameDialog(Gtk.Window):
    __gtype_name__ = 'DtoolDatasetNameDialog'

    name_label = Gtk.Template.Child()
    name_entry = Gtk.Template.Child()
    error_label = Gtk.Template.Child()

    def __init__(self, *args, **kwargs):
        self._on_confirmation = kwargs.pop('on_confirmation')
        super().__init__(*args, **kwargs)
        valid_chars = ' '.join(NAME_VALID_CHARS_LIST)
        self.name_label.set_text(
            f'Please provide a name for the new dataset. The name must be unique '
            f'to the local directory where the dataset is created but need not be '
            f'unique across a cloud storage system. The name may only contain the '
            f'following characters: {valid_chars}')
        self.name_entry.connect('changed', self._on_name_changed)

    def _on_name_changed(self, entry):
        """Clear the error state as the user edits the name."""
        self.error_label.hide()
        entry.get_style_context().remove_class('error')

    def _show_error(self, message):
        """Show an inline error message and highlight the entry."""
        self.error_label.set_text(message)
        self.error_label.show()
        self.name_entry.get_style_context().add_class('error')

    @Gtk.Template.Callback()
    def on_apply_clicked(self, widget):
        name = self.name_entry.get_text().strip()
        if not name:
            self._show_error('Please enter a name for the dataset.')
            return
        if not name_is_valid(name):
            valid_chars = ' '.join(NAME_VALID_CHARS_LIST)
            self._show_error(
                f'"{name}" is not a valid dataset name. '
                f'Only the following characters are allowed: {valid_chars}')
            return
        self._on_confirmation(name)
        self.destroy()

    @Gtk.Template.Callback()
    def on_cancel_clicked(self, widget):
        self.destroy()