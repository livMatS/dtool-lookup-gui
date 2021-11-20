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
import concurrent.futures
import logging
import os.path

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
        self.main_application = parent.main_application
        self.event_loop = parent.event_loop
        self.builder = parent.builder

        self._readme = None
        self._manifest = None

        self._sensitive = False

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
        self.rhs_dataset_list_auto_refresh = self.builder.get_object('rhs-dataset-list-auto-refresh')
        self.rhs_dataset_uri_entry_buffer = self.builder.get_object('rhs-dataset-uri-entry-buffer')
        self.rhs_dataset_uri_file_chooser_button = self.builder.get_object('rhs-dataset-uri-chooser-button')
        self.rhs_dtool_ls_results = self.builder.get_object('dtool-ls-results-rhs')
        self.statusbar_stack = self.builder.get_object('statusbar-stack')

        # models
        self.lhs_base_uri_inventory_group = parent.lhs_base_uri_inventory_group
        self.rhs_base_uri_inventory_group = parent.rhs_base_uri_inventory_group

        self.lhs_base_uri_inventory_group.append_dataset_list_box(self.lhs_dtool_ls_results)
        self.rhs_base_uri_inventory_group.append_dataset_list_box(self.rhs_dtool_ls_results)

        # self.lhs_base_uri_inventory_group.base_uri_selector.append_text_entry(self.lhs_base_uri_text_entry)
        # self.rhs_base_uri_inventory_group.base_uri_selector.append_text_entry(self.rhs_base_uri_text_entry)

        # self.lhs_base_uri_inventory_group.base_uri_selector.append_button(self.lhs_base_uri_apply_button)
        # self.lhs_base_uri_inventory_group.base_uri_selector.append_button(self.lhs_base_uri_apply_button)

        self.lhs_base_uri_inventory_group.base_uri_selector.append_file_chooser_button(
            self.lhs_base_uri_file_chooser_button)
        self.rhs_base_uri_inventory_group.base_uri_selector.append_file_chooser_button(
            self.rhs_base_uri_file_chooser_button)

        # self.lhs_base_uri_inventory_group.dataset_uri_selector.append_text_entry(self.lhs_dataset_uri_text_entry)
        # self.rhs_base_uri_inventory_group.dataset_uri_selector.append_text_entry(self.rhs_dataset_uri_text_entry)

        # self.lhs_base_uri_inventory_group.dataset_uri_selector.append_button(self.lhs_dataset_uri_apply_button)
        # self.lhs_base_uri_inventory_group.dataset_uri_selector.append_button(self.lhs_dataset_uri_apply_button)

        self.lhs_base_uri_inventory_group.dataset_uri_selector.append_file_chooser_button(
            self.lhs_dataset_uri_file_chooser_button)
        self.rhs_base_uri_inventory_group.dataset_uri_selector.append_file_chooser_button(
            self.rhs_dataset_uri_file_chooser_button)

        self.lhs_base_uri_inventory_group.append_auto_refresh_switch(self.lhs_dataset_list_auto_refresh)
        self.rhs_base_uri_inventory_group.append_auto_refresh_switch(self.rhs_dataset_list_auto_refresh)

        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)

    # signal handles
    def on_lhs_dataset_selected_from_list(self, list_box, list_box_row):
        """Select and display dataset when selected in left hand side list."""
        self.refresh()

    def on_rhs_dataset_selected_from_list(self, list_box, list_box_row):
        """Select and dataset when selected in right hand side list."""
        self.refresh()

    def on_dtool_copy_left_to_right_clicked(self,  button):
        """Copy lhs selected dataset to rhs selected base uri."""
        self.event_loop.create_task(self._dtool_copy_left_to_right())

    def on_dtool_copy_right_to_left_clicked(self,  button):
        """Copy lhs selected dataset to rhs selected base uri."""
        self.event_loop.create_task(self._dtool_copy_right_to_left())

    def refresh(self, page=None):
        """Update status bar and tab contents."""
        if not self._sensitive:
            return

        logger.debug("Refresh tab.")
        if self.lhs_base_uri_inventory_group.selected_uri is not None:
            lhs_msg = (f'{len(self.lhs_dtool_ls_results)} datasets - '
                       f'{self.lhs_base_uri_inventory_group.selected_uri}')
        elif self.lhs_base_uri_inventory_group.base_uri is not None:
            lhs_msg = (f'{len(self.lhs_dtool_ls_results)} '
                       f'datasets - {self.lhs_base_uri_inventory_group.base_uri}')
        else:
            lhs_msg = 'Specify left hand side base URI.'

        if self.rhs_base_uri_inventory_group.selected_uri is not None:
            rhs_msg = (f'{self.rhs_base_uri_inventory_group.selected_uri} - '
                       f'{len(self.rhs_dtool_ls_results)} datasets')
        elif self.rhs_base_uri_inventory_group.base_uri is not None:
            rhs_msg = (f'{self.rhs_base_uri_inventory_group.base_uri} - '
                       f'{len(self.rhs_dtool_ls_results)} datasets')
        else:
            rhs_msg = 'Specify right hand side base URI.'

        msg = ' : '.join((lhs_msg, rhs_msg))
        self.main_statusbar.push(0,msg)

    # private methods

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
        self.rhs_base_uri_inventory_group.refresh(selected_uri=target_dataset_uri)
        self.statusbar_stack.set_visible_child(self.main_statusbar)

    async def _dtool_copy_right_to_left(self):
        self.statusbar_stack.set_visible_child(self.main_progressbar)
        source_dataset_uri = self.rhs_dataset_uri_entry_buffer.get_text()
        target_base_uri = self.lhs_base_uri_entry_buffer.get_text()
        target_dataset_uri = self._copy_dataset(source_dataset_uri, target_base_uri)
        self.lhs_base_uri_inventory_group.refresh(selected_uri=target_dataset_uri)
        self.statusbar_stack.set_visible_child(self.main_statusbar)

    def set_sensitive(self, sensitive=True):
        self._sensitive = sensitive
