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
import graph_tool
import graph_tool.draw
import graph_tool.collection
import locale
import math
import os
import uuid
from contextlib import contextmanager
from datetime import date, datetime

import dtoolcore

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio

import gbulb

gbulb.install(gtk=True)

from .LookupClient import LookupClient


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
    returns strings.
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
    return '{:3.1f}{}{}'.format(val,
                                ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi'][
                                    magnitude], suffix)


def is_uuid(value):
    '''Check whether the data is a UUID.'''
    value = str(value)
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


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


def enumerate_uuids(data, key=[]):
    def enumerate_uuids_from_list(list_data, key):
        result = []
        for i, current_data in enumerate(list_data):
            entry = f'{i + 1}'
            if type(current_data) is list:
                result += enumerate_uuids_from_list(current_data,
                                                    key=key + [entry])
            elif type(current_data) is dict:
                result += enumerate_uuids(current_data, key=key + [entry])
            else:
                if is_uuid(current_data):
                    result += [(key + [entry], current_data)]
        return result

    result = []
    for entry, value in data.items():
        if type(value) is list:
            result += enumerate_uuids_from_list(value, key=key + [entry])
        elif type(value) is dict:
            result += enumerate_uuids(value, key=key + [entry])
        else:
            if is_uuid(value):
                result += [(key + [entry], value)]
    return result


def fill_manifest_tree_store(store, data, parent=None):
    for uuid, values in data.items():
        store.append(parent,
                     [values['relpath'],
                      human_readable_file_size(values['size_in_bytes']),
                      f'{date_to_string(values["utc_timestamp"])}',
                      uuid])


class Settings:
    def __init__(self):
        schema_source = Gio.SettingsSchemaSource.new_from_directory(
            os.path.dirname(__file__), Gio.SettingsSchemaSource.get_default(),
            False)
        schema = Gio.SettingsSchemaSource.lookup(
            schema_source, "de.uni-freiburg.dtool-gui", False)
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

        self._search_task = None

        self._selected_dataset = None
        self._readme = None
        self._manifest = None
        self._dependency_graph = None

        self.main_stack.set_visible_child(
            self.builder.get_object('main-spinner'))

    def _refresh_results(self):
        results_widget = self.builder.get_object('search-results')
        statusbar_widget = self.builder.get_object('main-statusbar')
        statusbar_widget.push(0, f'{len(self.datasets)} datasets')

        if len(self.datasets) == 0:
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
        self.manifest_stack.set_visible_child(
            self.builder.get_object('manifest-spinner'))

        manifest_view = self.builder.get_object('dataset-manifest')
        store = manifest_view.get_model()
        store.clear()
        self._manifest = await self.lookup.manifest(uri)
        fill_manifest_tree_store(store, self._manifest['items'])
        manifest_view.columns_autosize()
        manifest_view.show_all()

        self.manifest_stack.set_visible_child(
            self.builder.get_object('manifest-view'))

    async def _compute_dependencies(self, uri):
        uuid_to_vertex = {}

        async def _trace_dependency(uuid, shape='square'):
            v = self._dependency_graph.add_vertex()
            self._vertex_uuid[v] = uuid
            datasets = await self.lookup.by_uuid(uuid)
            if len(datasets) == 0:
                # This UUID does not exist in the database
                print(f'trace: UUID {uuid} does not exist')
                self._vertex_shape[v] = 'triangle'
                self._vertex_name[v] = 'Dataset does not exist in database.'
            else:
                # There may be the same dataset in multiple storage locations,
                # we just use the first
                self._vertex_shape[v] = shape
                dataset = datasets[0]
                self._vertex_name[v] = dataset['name']
                visited_uuids = set([])
                for path, uuid in enumerate_uuids(
                        await self.lookup.readme(dataset['uri'])):
                    if uuid not in visited_uuids:
                        if uuid in uuid_to_vertex:
                            # We have a Vertex for this UUID, simple add an
                            # edge
                            self._dependency_graph.add_edge(
                                uuid_to_vertex[uuid], v)
                        else:
                            # Create a new Vertex and continue tracing
                            visited_uuids.add(uuid)
                            uuid_to_vertex[uuid] = None
                            print('trace:', dataset['uuid'], '<-', uuid,
                                  'via README entry', path)
                            v2 = await _trace_dependency(uuid, shape='circle')
                            uuid_to_vertex[uuid] = v2
                            self._dependency_graph.add_edge(v2, v)
            return v

        print('Start computing dependencies')
        self.dependency_stack.set_visible_child(
            self.builder.get_object('dependency-spinner'))

        self._dependency_graph = graph_tool.Graph(directed=True)
        self._vertex_uuid = \
            self._dependency_graph.new_vertex_property('string')
        self._vertex_name = \
            self._dependency_graph.new_vertex_property('string')
        self._vertex_shape = \
            self._dependency_graph.new_vertex_property('string')

        # Compute dependency graph
        await _trace_dependency(self._selected_dataset['uuid'])

        # Create graph widget
        pos = graph_tool.draw.sfdp_layout(self._dependency_graph)
        graph_widget = graph_tool.draw.GraphWidget(
            self._dependency_graph, pos, vertex_size=20, vertex_pen_width=0,
            vertex_shape=self._vertex_shape,
            display_props=[self._vertex_uuid, self._vertex_name])
        dependency_view = self.builder.get_object('dependency-view')
        for child in dependency_view:
            child.destroy()
        dependency_view.pack_start(graph_widget, True, True, 0)
        graph_widget.fit_to_window()
        graph_widget.show()

        self.dependency_stack.set_visible_child(dependency_view)

        print('Finalized computing dependencies')

    async def connect(self):
        self.main_stack.set_visible_child(
            self.builder.get_object('main-spinner'))

        self.lookup = LookupClient(self.settings.lookup_url,
                                   self.settings.authenticator_url,
                                   self.settings.username,
                                   self.settings.password)
        await self.lookup.connect()
        self.datasets = await self.lookup.all()
        self._refresh_results()

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
                else:
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


def run_gui():
    builder = Gtk.Builder()
    builder.add_from_file(os.path.dirname(__file__) + '/dtool-gui.glade')

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

    # Connect to the lookup server upon startup
    loop.create_task(signal_handler.connect())

    loop.run_forever()
