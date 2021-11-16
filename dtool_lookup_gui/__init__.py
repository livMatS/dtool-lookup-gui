#
# Copyright 2020, 2021 Lars Pastewka, Johannes Hoermann
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
import math
import os
import uuid
from contextlib import contextmanager
from datetime import date, datetime

from ruamel.yaml import YAML
from ruamel.yaml.parser import ParserError
from ruamel.yaml.constructor import DuplicateKeyError
from ruamel.yaml.scanner import ScannerError

import dtoolcore


@contextmanager
def time_locale(name):
    # This code snippet was taken from:
    # https://stackoverflow.com/questions/18593661/how-do-i-strftime-a-date-object-in-a-different-locale
    saved = locale.setlocale(locale.LC_TIME)
    try:
        yield locale.setlocale(locale.LC_TIME, name)
    finally:
        locale.setlocale(locale.LC_TIME, saved)


def is_uuid(value):
    '''Check whether the data is a UUID.'''
    value = str(value)
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


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
            if isinstance(current_data, list):
                current_parent = store.append(parent,
                                              [entry, None, False, None])
                fill_readme_tree_store_from_list(store, current_data,
                                                 parent=current_parent)
            elif isinstance(current_data, dict):
                current_parent = store.append(parent,
                                              [entry, None, False, None])
                fill_readme_tree_store(store, current_data,
                                       parent=current_parent)
            else:
                append_entry(store, entry, current_data, parent)

    if data is not None:
        for entry, value in data.items():
            if isinstance(value, list):
                current = store.append(parent,
                                       [entry, None, False, None])
                fill_readme_tree_store_from_list(store, value, parent=current)
            elif isinstance(value, dict):
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


def _validate_readme(readme_content):
    """Return (YAML string, error message)."""
    yaml = YAML()
    # Ensure that the content is valid YAML.
    try:
        readme_formatted = yaml.load(readme_content)
        return readme_formatted, None
    except (ParserError, DuplicateKeyError, ScannerError) as message:
        return None, str(message)