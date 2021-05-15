#
# Copyright 2020 Lars Pastewka
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
import concurrent.futures
import locale
import math
import os
import shutil
import subprocess
from contextlib import contextmanager
from datetime import date, datetime
from functools import reduce

import dtoolcore
import dtool_lookup_api.core.config
from dtool_lookup_api.core.LookupClient import ConfigurationBasedLookupClient as LookupClient
dtool_lookup_api.core.config.Config.interactive = False

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio

import gbulb

gbulb.install(gtk=True)

from .Dependencies import DependencyGraph, is_uuid
from .GraphWidget import GraphWidget

def open(filename):
    """Open file in system-default application"""


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
    Convert a sting or a timestamp to a timestamp. This is a dirty fix necessary
    because the /dataset/list route return timestamps but /dataset/search
    returns strings in older versions of the lookup server (before 0.15.0).
    """
    if type(d) is str:
        try:
            with time_locale('C'):
                d = dtoolcore.utils.timestamp(
                    datetime.strptime(d, '%a, %d %b %Y %H:%M:%S %Z'))
        except ValueError as e:
            d = -1
    return d


def datetime_to_string(d):
    return datetime.fromtimestamp(to_timestamp(d))


def date_to_string(d):
    return date.fromtimestamp(to_timestamp(d))


def human_readable_file_size(num, suffix='B'):
    # From: https://gist.github.com/cbwar/d2dfbc19b140bd599daccbe0fe925597
    if num == 0:
        return '0B'
    magnitude = int(math.floor(math.log(num, 1024)))
    val = num / math.pow(1024, magnitude)
    if magnitude > 7:
        return '{:.1f}{}{}'.format(val, 'Yi', suffix)
    return '{:3.1f}{}{}'.format(val, ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi'][magnitude], suffix)


def fill_readme_tree_store(store, data, parent=None):
    def append_entry(store, entry, value, parent):
        # Check whether the data is a UUID. We then enable a
        # hyperlink-like navigation between datasets
        is_u = is_uuid(value)
        if is_u:
            markup = '<span foreground="blue" underline="single">' \
                     f'{str(value)}</span>'
        else:
            markup = f'<span>{str(value)}</span>'
        store.append(parent,
                     [entry, str(value), is_u, markup])

    def fill_readme_tree_store_from_list(store, list_data, parent=None):
        for i, current_data in enumerate(list_data):
            entry = f'{i + 1}'
            if type(current_data) is list:
                current_parent = store.append(parent,
                                              [entry, None, False, None])
                fill_readme_tree_store_from_list(store, current_data,
                                                 parent=current_parent)
            elif type(current_data) is dict:
                current_parent = store.append(parent,
                                              [entry, None, False, None])
                fill_readme_tree_store(store, current_data,
                                       parent=current_parent)
            else:
                append_entry(store, entry, current_data, parent)

    if data is not None:
        for entry, value in data.items():
            if type(value) is list:
                current = store.append(parent,
                                       [entry, None, False, None])
                fill_readme_tree_store_from_list(store, value, parent=current)
            elif type(value) is dict:
                current = store.append(parent,
                                       [entry, None, False, None])
                fill_readme_tree_store(store, value, parent=current)
            else:
                append_entry(store, entry, value, parent)


def fill_manifest_tree_store(store, data, parent=None):
    nodes = {}

    def find_or_create_parent_node(path, top_parent):
        if not path:
            return top_parent
        try:
            return nodes[path]
        except KeyError:
            head, tail = os.path.split(path)
            parent = find_or_create_parent_node(head, top_parent)
            new_node = store.append(parent, [tail, '', '', ''])
            nodes[path] = new_node
            return new_node

    for uuid, values in sorted(data.items(), key=lambda kv: kv[1]['relpath']):
        head, tail = os.path.split(values['relpath'])
        store.append(find_or_create_parent_node(head, parent),
                     [tail,
                      human_readable_file_size(values['size_in_bytes']),
                      f'{date_to_string(values["utc_timestamp"])}',
                      uuid])


class Settings:
    def __init__(self):
        schema_source = Gio.SettingsSchemaSource.new_from_directory(
            os.path.dirname(__file__), Gio.SettingsSchemaSource.get_default(),
            False)
        schema = Gio.SettingsSchemaSource.lookup(
            schema_source, "de.uni-freiburg.dtool-lookup-gui", False)
        self.settings = Gio.Settings.new_full(schema, None, None)

    @property
    def lookup_url(self):
        return self.settings.get_string('lookup-url')

    @property
    def authenticator_url(self):
        return self.settings.get_string('authenticator-url')

    @property
    def username(self):
        return self.settings.get_string('lookup-username')

    @property
    def password(self):
        return self.settings.get_string('lookup-password')

    @property
    def dependency_keys(self):
        return self.settings.get_string('dependency-keys')


class SignalHandler:
    def __init__(self, event_loop, builder, settings):
        self.event_loop = event_loop
        self.builder = builder
        self.settings = settings
        self.lookup = None

        self.main_window = self.builder.get_object('main-window')
        self.settings_window = self.builder.get_object('settings-window')

        self.main_stack = self.builder.get_object('main-stack')
        self.readme_stack = self.builder.get_object('readme-stack')
        self.manifest_stack = self.builder.get_object('manifest-stack')
        self.dependency_stack = self.builder.get_object('dependency-stack')

        self.error_bar = self.builder.get_object('error-bar')
        self.error_label = self.builder.get_object('error-label')

        self.error_bar.set_revealed(False)

        self._search_task = None

        self._selected_dataset = None
        self._readme = None
        self._manifest = None

        self.main_stack.set_visible_child(
            self.builder.get_object('main-spinner'))

        self.datasets = None
        self.server_config = None

        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)

    def _refresh_results(self):
        results_widget = self.builder.get_object('search-results')
        statusbar_widget = self.builder.get_object('main-statusbar')
        if self.datasets is not None and self.server_config:
            statusbar_widget.push(0, f'{len(self.datasets)} datasets - '
                                     f'Connected to lookup server version '
                                     f"{self.server_config['version']}")
            if len(self.datasets) == 0:
                self.main_stack.set_visible_child(
                    self.builder.get_object('main-not-found'))
                return
        else:
            statusbar_widget.push(0, 'Server connection failed')
            self.main_stack.set_visible_child(
                self.builder.get_object('main-not-found'))
            return

        for entry in results_widget:
            entry.destroy()
        first_row = None
        for dataset in sorted(self.datasets,
                              key=lambda d: -to_timestamp(d['frozen_at'])):
            row = Gtk.ListBoxRow()
            if first_row is None:
                first_row = row
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            label = Gtk.Label(xalign=0)
            label.set_markup(f'<b>{dataset["uuid"]}</b>')
            vbox.pack_start(label, True, True, 0)
            label = Gtk.Label(xalign=0)
            label.set_markup(f'{dataset["name"]}')
            vbox.pack_start(label, True, True, 0)
            label = Gtk.Label(xalign=0)
            label.set_markup(
                f'<small>Created by: {dataset["creator_username"]}, '
                f'frozen at: '
                f'{date_to_string(dataset["frozen_at"])}</small>')
            vbox.pack_start(label, True, True, 0)
            row.dataset = dataset
            row.add(vbox)
            results_widget.add(row)
        results_widget.select_row(first_row)
        results_widget.show_all()

        self.main_stack.set_visible_child(
            self.builder.get_object('main-view'))

    async def _fetch_readme(self, uri):
        self.error_bar.set_revealed(False)
        self.readme_stack.set_visible_child(
            self.builder.get_object('readme-spinner'))

        readme_view = self.builder.get_object('dataset-readme')
        store = readme_view.get_model()
        store.clear()
        self._readme = await self.lookup.readme(uri)
        fill_readme_tree_store(store, self._readme)
        readme_view.columns_autosize()
        readme_view.show_all()

        self.readme_stack.set_visible_child(
            self.builder.get_object('readme-view'))

    async def _fetch_manifest(self, uri):
        self.error_bar.set_revealed(False)
        self.manifest_stack.set_visible_child(
            self.builder.get_object('manifest-spinner'))

        manifest_view = self.builder.get_object('dataset-manifest')
        store = manifest_view.get_model()
        store.clear()
        self._manifest = await self.lookup.manifest(uri)
        try:
            fill_manifest_tree_store(store, self._manifest['items'])
        except Exception as e:
            print(e)
        manifest_view.columns_autosize()
        manifest_view.show_all()

        self.manifest_stack.set_visible_child(
            self.builder.get_object('manifest-view'))

    async def _compute_dependencies(self, uri):
        self.error_bar.set_revealed(False)
        self.dependency_stack.set_visible_child(
            self.builder.get_object('dependency-spinner'))

        # Compute dependency graph
        self._dependency_graph = DependencyGraph()
        await self._dependency_graph.trace_dependencies(
            self.lookup, self._selected_dataset['uuid'],
            dependency_keys=self.settings.dependency_keys)

        # Show message if uuids are missing
        missing_uuids = self._dependency_graph.missing_uuids
        if missing_uuids:
            self.show_error('The following UUIDs were found during dependency graph calculation but are not present '
                            'in the database: {}'.format(reduce(lambda a, b: a + ', ' + b, missing_uuids)))

        # Create graph widget
        graph_widget = GraphWidget(self.builder, self._dependency_graph.graph)
        dependency_view = self.builder.get_object('dependency-view')
        for child in dependency_view:
            child.destroy()
        dependency_view.pack_start(graph_widget, True, True, 0)
        graph_widget.show()

        self.dependency_stack.set_visible_child(dependency_view)

    async def connect(self):
        self.error_bar.set_revealed(False)
        self.main_stack.set_visible_child(
            self.builder.get_object('main-spinner'))

        self.lookup = LookupClient(lookup_url=self.settings.lookup_url,
                                   auth_url=self.settings.authenticator_url,
                                   username=self.settings.username,
                                   password=self.settings.password,
                                   verify_ssl=False)
        try:
            await self.lookup.connect()
            self.server_config = await self.lookup.config()
            if 'msg' in self.server_config:
                self.show_error(self.server_config['msg'])
            self.datasets = await self.lookup.all()
        except Exception as e:
            self.show_error(str(e))
            self.datasets = []
        self._refresh_results()

    def show_error(self, msg):
        self.error_label.set_text(msg)
        self.error_bar.show()
        self.error_bar.set_revealed(True)

    def on_window_destroy(self, *args):
        self.event_loop.stop()

    def on_result_selected(self, list_box, list_box_row):
        if list_box_row is None:
            return
        self._selected_dataset = list_box_row.dataset
        self._readme = None
        self._manifest = None
        self._dependency_graph = None

        self.builder.get_object('dataset-name').set_text(
            self._selected_dataset['name'])
        self.builder.get_object('dataset-uuid').set_text(
            self._selected_dataset['uuid'])
        self.builder.get_object('dataset-uri').set_text(
            self._selected_dataset['uri'])
        self.builder.get_object('dataset-created-by').set_text(
            self._selected_dataset['creator_username'])
        self.builder.get_object('dataset-created-at').set_text(
            f'{datetime_to_string(self._selected_dataset["created_at"])}')
        self.builder.get_object('dataset-frozen-at').set_text(
            f'{datetime_to_string(self._selected_dataset["frozen_at"])}')

        page = self.builder.get_object('dataset-notebook').get_property('page')
        if page == 0:
            self._readme_task = asyncio.ensure_future(
                self._fetch_readme(self._selected_dataset['uri']))
        elif page == 1:
            self._manifest_task = asyncio.ensure_future(
                self._fetch_manifest(self._selected_dataset['uri']))
        elif page == 2:
            self._dependency_task = asyncio.ensure_future(
                self._compute_dependencies(self._selected_dataset['uri']))

    def on_search(self, search_entry):
        self.main_stack.set_visible_child(
            self.builder.get_object('main-spinner'))

        async def fetch_search_result(keyword):
            if keyword:
                if keyword.startswith('uuid:'):
                    self.datasets = await self.lookup.by_uuid(keyword[5:])
                elif keyword.startswith('{') and keyword.endswith('}'):
                    # TODO: replace with proper syntax check on mongo query
                    self.datasets = await self.lookup.by_query(keyword)
                else:
                    # NOTE: server side allows a dict with the key-value pairs
                    # "free_text", "creator_usernames", "base_uris", "uuids", "tags",
                    # via route '/dataset/search', where all except "free_text"
                    # can be lists and are translated to logical "and" or "or"
                    # constructs on the server side. With the special treatment
                    # of the 'uuid' keyword above, should we introduce similar
                    # options for the other available keywords?
                    self.datasets = await self.lookup.search(keyword)
            else:
                self.datasets = await self.lookup.all()
            self._refresh_results()

        if self._search_task is not None:
            self._search_task.cancel()
        self._search_task = asyncio.ensure_future(
            fetch_search_result(search_entry.get_text()))

    def on_settings_clicked(self, user_data):
        self.settings_window.show()

    def on_delete_settings(self, event, user_data):
        self.settings_window.hide()
        # Reconnect since settings may have been changed
        asyncio.ensure_future(self.connect())
        return True

    def on_switch_page(self, notebook, page, page_num):
        if self._selected_dataset is not None:
            if page_num == 0 and self._readme is None:
                self._readme_task = asyncio.ensure_future(
                    self._fetch_readme(self._selected_dataset['uri']))
            elif page_num == 1 and self._manifest is None:
                self._manifest_task = asyncio.ensure_future(
                    self._fetch_manifest(self._selected_dataset['uri']))
            elif page_num == 2 and self._dependency_graph is None:
                self._dependency_task = asyncio.ensure_future(
                    self._compute_dependencies(self._selected_dataset['uri']))

    def on_readme_row_activated(self, tree_view, path, column):
        store = tree_view.get_model()
        iter = store.get_iter(path)
        is_uuid = store.get_value(iter, 2)
        if is_uuid:
            uuid = store.get_value(iter, 1)
            self.builder.get_object('search-entry').set_text(f'uuid:{uuid}')
            return True
        return False

    def dtool_retrieve_item(self, uri, item_name, item_uuid):
        dataset = dtoolcore.DataSet.from_uri(uri)
        if item_uuid in dataset.identifiers:
            shutil.copyfile(dataset.item_content_abspath(item_uuid),
                            f'/home/pastewka/Downloads/{item_name}')
            subprocess.run(["xdg-open", f'/home/pastewka/Downloads/{item_name}'])
            # The following lines should be more portable but don't run
            #Gio.AppInfo.launch_default_for_uri(
            #    dataset.item_content_abspath(uuid))
        else:
            self.show_error(f'Cannot open item {item_name}, since the UUID {uuid_name} '
                            'appears to exist in the lookup server only.')

    async def retrieve_item(self, uri, item_name, item_uuid):
        loop = asyncio.get_event_loop()
        await asyncio.wait([
            loop.run_in_executor(self.thread_pool, self.dtool_retrieve_item,
                                 uri, item_name, item_uuid)])

    def on_manifest_row_activated(self, tree_view, path, column):
        store = tree_view.get_model()
        iter = store.get_iter(path)
        item = store.get_value(iter, 0)
        uuid = store.get_value(iter, 3)
        asyncio.ensure_future(
            self.retrieve_item(self._selected_dataset['uri'], item, uuid))

def run_gui():
    builder = Gtk.Builder()
    builder.add_from_file(os.path.dirname(__file__) + '/dtool-lookup-gui.glade')

    loop = asyncio.get_event_loop()

    settings = Settings()

    signal_handler = SignalHandler(loop, builder, settings)
    builder.connect_signals(signal_handler)

    builder.get_object('main-window').show_all()

    settings.settings.bind("lookup-url", builder.get_object('lookup-url-entry'),
                           'text', Gio.SettingsBindFlags.DEFAULT)
    settings.settings.bind("authenticator-url",
                           builder.get_object('authenticator-url-entry'),
                           'text', Gio.SettingsBindFlags.DEFAULT)
    settings.settings.bind("lookup-username",
                           builder.get_object('username-entry'), 'text',
                           Gio.SettingsBindFlags.DEFAULT)
    settings.settings.bind("lookup-password",
                           builder.get_object('password-entry'), 'text',
                           Gio.SettingsBindFlags.DEFAULT)
    settings.settings.bind("dependency-keys",
                           builder.get_object('dependency-keys'), 'text',
                           Gio.SettingsBindFlags.DEFAULT)

    # Connect to the lookup server upon startup
    loop.create_task(signal_handler.connect())

    loop.run_forever()
