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
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Gio
import concurrent.futures
import logging
import os.path
import urllib.parse

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import dtoolcore

from .dtool_gtk import ProgressBar

from . import GlobalConfig

HOME_DIR = os.path.expanduser("~")

logger = logging.getLogger(__name__)


class SignalHandler:
    def __init__(self, parent):
        self.event_loop = parent.event_loop
        self.builder = parent.builder

        self._readme = None
        self._manifest = None

        # gui elements, alphabetically
        self.dtool_copy_left_to_right_button = self.builder.get_object('dtool-copy-left-to-right')
        self.dtool_copy_right_to_left_button = self.builder.get_object('dtool-copy-right-to-left')
        self.error_bar = self.builder.get_object('error-bar')
        self.error_label = self.builder.get_object('error-label')
        self.lhs_base_uri_entry_buffer = self.builder.get_object('lhs-base-uri-entry-buffer')
        self.lhs_base_uri_file_chooser_button = self.builder.get_object('lhs-base-uri-chooser-button')
        self.lhs_dataset_list_auto_refresh = self.builder.get_object('lhs-dataset-list-auto-refresh')
        self.lhs_dataset_uri_entry_buffer = self.builder.get_object('lhs-dataset-uri-entry-buffer')
        self.lhs_dataset_uri_file_chooser_button = self.builder.get_object('lhs-dataset-uri-chooser-button')
        self.lhs_dtool_ls_results = self.builder.get_object('dtool-ls-results-lhs')
        self.main_progressbar = self.builder.get_object('main-progressbar')
        self.main_statusbar = self.builder.get_object('main-statusbar')
        self.rhs_base_uri_entry_buffer = self.builder.get_object('rhs-base-uri-entry-buffer')
        self.rhs_base_uri_file_chooser_button = self.builder.get_object('rhs-base-uri-chooser-button')
        self.rhs_dataset_list_auto_refresh = self.builder.get_object('lhs-dataset-list-auto-refresh')
        self.rhs_dataset_uri_entry_buffer = self.builder.get_object('rhs-dataset-uri-entry-buffer')
        self.rhs_dataset_uri_file_chooser_button = self.builder.get_object('rhs-dataset-uri-chooser-button')
        self.rhs_dtool_ls_results = self.builder.get_object('dtool-ls-results-rhs')
        self.statusbar_stack = self.builder.get_object('statusbar-stack')

        # models
        self.lhs_dtool_ls_results.dataset_list_model = parent.lhs_dataset_list_model
        self.rhs_dtool_ls_results.dataset_list_model = parent.rhs_dataset_list_model

        # configure
        self.lhs_dataset_list_auto_refresh.set_active(GlobalConfig.auto_refresh_on)
        self.rhs_dataset_list_auto_refresh.set_active(GlobalConfig.auto_refresh_on)
        self.lhs_dtool_ls_results.auto_refresh = GlobalConfig.auto_refresh_on
        self.rhs_dtool_ls_results.auto_refresh = GlobalConfig.auto_refresh_on

        initial_lhs_base_uri = self.lhs_dtool_ls_results.base_uri
        if initial_lhs_base_uri is None:
            initial_lhs_base_uri = HOME_DIR
        self._set_lhs_base_uri(initial_lhs_base_uri)

        initial_rhs_base_uri = self.rhs_dtool_ls_results.base_uri
        if initial_rhs_base_uri is None:
            initial_rhs_base_uri = HOME_DIR
        self._set_rhs_base_uri(initial_rhs_base_uri)

        self.lhs_dtool_ls_results.refresh()
        self.rhs_dtool_ls_results.refresh()

        try:
            self.lhs_dtool_ls_results.dataset_list_model.set_active_index(0)
        except IndexError as exc:
            pass # Empty list, ignore

        try:
            self.rhs_dtool_ls_results.dataset_list_model.set_active_index(0)
        except IndexError as exc:
            pass # Empty list, ignore

        lhs_dataset_uri = self.lhs_dtool_ls_results.selected_uri
        # print(self.dataset_list_model.base_uri)
        if lhs_dataset_uri is not None:
            self._set_lhs_dataset_uri(lhs_dataset_uri)
            #  self._select_lhs_dataset(lhs_dataset_uri)

        rhs_dataset_uri = self.rhs_dtool_ls_results.selected_uri
        if rhs_dataset_uri is not None:
            self._set_rhs_dataset_uri(rhs_dataset_uri)
            # self._select_rhs_dataset(rhs_dataset_uri)

        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)

        self.refresh()

    # signal handles

    def on_lhs_base_uri_set(self,  filechooserbutton):
        """Base URI directory selected with file chooser."""
        base_uri = filechooserbutton.get_uri()
        self._set_lhs_base_uri(base_uri)

    def on_rhs_base_uri_set(self,  filechooserbutton):
        """Base URI directory selected with file chooser."""
        base_uri = filechooserbutton.get_uri()
        self._set_rhs_base_uri(base_uri)

    def on_lhs_base_uri_open(self,  button):
        """Open base URI button clicked."""
        self.lhs_dtool_ls_results.refresh()

    def on_rhs_base_uri_open(self,  button):
        """Open base URI button clicked."""
        self.rhs_dtool_ls_results.refresh()

    def on_lhs_dataset_uri_set(self,  filechooserbutton):
        self._set_lhs_dataset_uri(filechooserbutton.get_uri())

    def on_rhs_dataset_uri_set(self,  filechooserbutton):
        self._set_rhs_dataset_uri(filechooserbutton.get_uri())

    def on_lhs_dataset_uri_open(self,  button):
        """Select and display dataset when URI specified in text box 'dataset URI' and button 'open' clicked."""
        self.lhs_dtool_ls_results.refresh()
        self.refresh()

    def on_rhs_dataset_uri_open(self,  button):
        """Select and display dataset when URI specified in text box 'dataset URI' and button 'open' clicked."""
        self.rhs_dtool_ls_results.refresh()
        self.refresh()

    def on_lhs_dataset_selected_from_list(self, list_box, list_box_row):
        """Select and display dataset when selected in left hand side list."""
        if list_box_row is None:
            return
        uri = list_box_row.dataset['uri']
        # self.lhs_dtool_ls_results.selected_uri = uri
        self._set_lhs_dataset_uri(uri)
        self.lhs_dataset_uri_entry_buffer.set_text(uri, -1)
        self.refresh()

    def on_rhs_dataset_selected_from_list(self, list_box, list_box_row):
        """Select and dataset when selected in right hand side list."""
        if list_box_row is None:
            return
        uri = list_box_row.dataset['uri']
        # self.rhs_dtool_ls_results.selected_uri = uri
        self._set_rhs_dataset_uri(uri)
        self.rhs_dataset_uri_entry_buffer.set_text(uri, -1)
        self.refresh()

    def on_lhs_dataset_list_auto_refresh_toggled(self, checkbox):
        self.lhs_dtool_ls_results.auto_refresh = checkbox.get_active()
        self.lhs_dtool_ls_results.refresh()

    def on_rhs_dataset_list_auto_refresh_toggled(self, checkbox):
        self.rhs_dtool_ls_results.auto_refresh = checkbox.get_active()
        self.rhs_dtool_ls_results.refresh()

    def on_dtool_copy_left_to_right_clicked(self,  button):
        """Copy lhs selected dataset to rhs selected base uri."""
        self.event_loop.create_task(self._dtool_copy_left_to_right())

    def on_dtool_copy_right_to_left_clicked(self,  button):
        """Copy lhs selected dataset to rhs selected base uri."""
        self.event_loop.create_task(self._dtool_copy_right_to_left())

    def refresh(self, page=None):
        """Update status bar and tab contents."""

        logger.debug("Refresh tab.")
        if self.lhs_dtool_ls_results.selected_uri is not None:
            lhs_msg = (f'{len(self.lhs_dtool_ls_results)} datasets - '
                       f'{self.lhs_dtool_ls_results.selected_uri}')
        elif self.lhs_dtool_ls_results.base_uri is not None:
            lhs_msg = (f'{len(self.lhs_dtool_ls_results)} '
                       f'datasets - {self.lhs_dtool_ls_results.base_uri}')
        else:
            lhs_msg = 'Specify left hand side base URI.'

        if self.rhs_dtool_ls_results.selected_uri is not None:
            rhs_msg = (f'{self.rhs_dtool_ls_results.selected_uri} - '
                       f'{len(self.rhs_dtool_ls_results)} datasets')
        elif self.rhs_dtool_ls_results.base_uri is not None:
            rhs_msg = (f'{self.rhs_dtool_ls_results.base_uri} - '
                       f'{len(self.rhs_dtool_ls_results)} datasets')
        else:
            rhs_msg = 'Specify right hand side base URI.'

        msg = ' : '.join((lhs_msg, rhs_msg))
        self.main_statusbar.push(0,msg)

    # private methods
    def _set_lhs_base_uri(self, uri):
        """Sets lhs base uri and associated file chooser and input field."""
        p = urllib.parse.urlparse(uri)
        fpath = os.path.abspath(os.path.join(p.netloc, p.path))

        if os.path.isdir(fpath):
            fpath = os.path.abspath(fpath)
            self.lhs_base_uri_file_chooser_button.set_current_folder(fpath)

    def _set_rhs_base_uri(self, uri):
        """Set dataset file chooser and input field."""
        p = urllib.parse.urlparse(uri)
        fpath = os.path.abspath(os.path.join(p.netloc, p.path))

        if os.path.isdir(fpath):
            fpath = os.path.abspath(fpath)
            self.rhs_base_uri_file_chooser_button.set_current_folder(fpath)

    def _set_lhs_dataset_uri(self, uri):
        """Set dataset file chooser and input field."""
        p = urllib.parse.urlparse(uri)
        fpath = os.path.abspath(os.path.join(p.netloc, p.path))

        if os.path.isdir(fpath):
            fpath = os.path.abspath(fpath)
            self.lhs_dataset_uri_file_chooser_button.set_current_folder(fpath)

    def _set_rhs_dataset_uri(self, uri):
        """Set dataset file chooser and input field."""
        p = urllib.parse.urlparse(uri)
        fpath = os.path.abspath(os.path.join(p.netloc, p.path))

        if os.path.isdir(fpath):
            fpath = os.path.abspath(fpath)
            self.rhs_dataset_uri_file_chooser_button.set_current_folder(fpath)

    # TODO: jlh, I really don't know hat I am doing here, just copy & paste
    # def _async_copy_dataset(self, *args, **kwargs):
    #    loop = asyncio.get_event_loop()
    #    await asyncio.wait([
    #        loop.run_in_executor(self.thread_pool, self._copy_dataset, *args, **kwargs)])

    def _copy_dataset(self, source_dataset_uri, target_base_uri, resume=False, auto_resume=True):
        """Copy a dataset."""

        # TODO: try to copy without resume flag, if failed, then ask whether
        # try to resume

        src_dataset = dtoolcore.DataSet.from_uri(source_dataset_uri)

        dest_uri = dtoolcore._generate_uri(
            admin_metadata=src_dataset._admin_metadata,
            base_uri=target_base_uri
        )

        copy_func = dtoolcore.copy
        is_dataset = dtoolcore._is_dataset(dest_uri, config_path=None)
        if resume or (auto_resume and is_dataset):
            # copy resume
            copy_func = dtoolcore.copy_resume
        elif is_dataset:
            # don't resume
            raise FileExistsError("Dataset already exists: {}".format(dest_uri))
        else:
            # If the destination URI is a "file" dataset one needs to check if
            # the path already exists and exit gracefully if true.
            parsed_dataset_uri = dtoolcore.utils.generous_parse_uri(dest_uri)
            if parsed_dataset_uri.scheme == "file":
                if os.path.exists(parsed_dataset_uri.path):
                    raise FileExistsError(
                        "Path already exists: {}".format(parsed_dataset_uri.path))

        num_items = len(list(src_dataset.identifiers))

        with ProgressBar(length=num_items * 2,
                         label="Copying dataset",
                         pb=self.main_progressbar) as progressbar:
            dest_uri = copy_func(
                src_uri=source_dataset_uri,
                dest_base_uri=target_base_uri,
                config_path=None,
                progressbar=progressbar
            )

        return dest_uri

    # asynchronous methods
    async def _dtool_copy_left_to_right(self):
        self.statusbar_stack.set_visible_child(self.main_progressbar)
        source_dataset_uri = self.lhs_dataset_uri_entry_buffer.get_text()
        target_base_uri = self.rhs_base_uri_entry_buffer.get_text()
        target_dataset_uri = self._copy_dataset(source_dataset_uri, target_base_uri)
        self.rhs_dtool_ls_results.refresh(selected_uri=target_dataset_uri)
        self.statusbar_stack.set_visible_child(self.main_statusbar)

    async def _dtool_copy_right_to_left(self):
        self.statusbar_stack.set_visible_child(self.main_progressbar)
        source_dataset_uri = self.rhs_dataset_uri_entry_buffer.get_text()
        target_base_uri = self.lhs_base_uri_entry_buffer.get_text()
        target_dataset_uri = self._copy_dataset(source_dataset_uri, target_base_uri)
        self.lhs_dtool_ls_results.refresh(selected_uri=target_dataset_uri)
        self.statusbar_stack.set_visible_child(self.main_statusbar)

    # general-purpose methods
    def show_error(self, msg):
        self.error_label.set_text(msg)
        self.error_bar.show()
        self.error_bar.set_revealed(True)

    def set_sensitive(self, sensitive=True):
        pass