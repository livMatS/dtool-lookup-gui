#
# Copyright 2021 Johannes Hoermann
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
import asyncio
import logging


import gi
gi.require_version('GtkSource', '4')
from gi.repository import Gtk, Gdk, Gio, GObject, GtkSource

from .. import _standardize_readme

GObject.type_register(GtkSource.View)

logger = logging.getLogger(__name__)

class SignalHandler:
    def __init__(self, parent):
        self.main_application = parent.main_application
        self.event_loop = parent.event_loop
        self.builder = parent.builder
        self.settings = parent.settings

        self.metadata_dialog = self.builder.get_object('metadata-dialog')
        self.metadata_editor = self.builder.get_object('metadata-editor')
        self.metadata_buffer = self.metadata_editor.get_buffer()

        self.lhs_base_uri_inventory_group = parent.lhs_base_uri_inventory_group

        self.lang_manager = GtkSource.LanguageManager()
        self.metadata_buffer.set_language(self.lang_manager.get_language("yaml"))
        self.metadata_buffer.set_highlight_syntax(True)
        self.metadata_buffer.set_highlight_matching_brackets(True)

        self._dataset = None
        self._readme_task = None

    def show(self):
        self._readme_task = asyncio.create_task(self._fetch_readme())
        self.metadata_dialog.show()

    # signal handlers
    def on_metadata_editor_apply_clicked(self, button):
        try:
            self._put_readme()
        except ValueError as err:
            dialog = Gtk.MessageDialog(
                transient_for=self.metadata_dialog,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Error in metadata",
            )
            dialog.format_secondary_text(err.__str__())
            dialog.run()
            dialog.destroy()
        else:
            self.metadata_dialog.hide()
            self.main_application.direct_tab._mark_dataset_as_changed()  # ugly, enforces readme reload
            self.main_application.refresh()

    def on_metadata_editor_cancel_clicked(self, button):
        self.metadata_dialog.hide()

    # private methods
    def _put_readme(self):
        start_iter = self.metadata_buffer.get_start_iter()
        end_iter = self.metadata_buffer.get_end_iter()
        readme_content = self.metadata_buffer.get_text(start_iter, end_iter, True)
        logger.debug(f"Put raw content '{readme_content}'")
        logger.debug(f"  to README content to {self._dataset.uri}.")
        try:
            validated_readme_content = _standardize_readme(readme_content)
        except ValueError as exc:
            raise  # display dialog
        if validated_readme_content is not None:
            logger.debug(f"Put processed content '{validated_readme_content}'")
        asyncio.create_task(self._async_put_readme(validated_readme_content))



    async def _fetch_readme(self):
        self._dataset = self.lhs_base_uri_inventory_group.dataset_model.dataset
        logger.debug(f"Fetch README content from {self._dataset.uri}.")
        readme_content = self._dataset.get_readme_content()
        logger.debug(f"Got content '{readme_content}'.")
        self.metadata_buffer.set_text(readme_content, -1)

    async def _async_put_readme(self, readme_content):
        self._dataset.put_readme(readme_content)
#
