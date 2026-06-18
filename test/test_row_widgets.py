#
# Copyright 2026 Johannes Laurin Hörmann
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
"""Unit tests for the dataset and base-URI list-box row widgets.

Both are plain Gtk.ListBoxRow subclasses that build their contents in __init__,
so they are constructed directly with lightweight stand-in models.
"""
from dtool_lookup_gui.widgets.dataset_row import DtoolDatasetRow
from dtool_lookup_gui.widgets.base_uri_row import DtoolBaseURIRow
from dtool_lookup_gui.models.base_uris import LocalBaseURIModel, S3BaseURIModel


class FakeDataset:
    def __init__(self, is_frozen):
        self.is_frozen = is_frozen
        self.uuid = "1234-uuid"
        self.name = "my_dataset"
        self.creator = "alice"
        self.date = "2023-05-11"
        self.size_str = " 1.2 kB "

    def freeze(self):
        self.is_frozen = True


# ===========================================================================
# DtoolDatasetRow
# ===========================================================================

def test_dataset_row_frozen_shows_uuid_and_details():
    row = DtoolDatasetRow(FakeDataset(is_frozen=True))
    assert "1234-uuid" in row.uuid_label.get_label()
    assert "*" not in row.uuid_label.get_label()
    assert "my_dataset" in row.name_label.get_label()
    assert "frozen at" in row.info_label.get_label()
    assert "alice" in row.info_label.get_label()


def test_dataset_row_proto_is_marked_and_not_yet_frozen():
    row = DtoolDatasetRow(FakeDataset(is_frozen=False))
    assert "* " in row.uuid_label.get_label()  # proto datasets are starred
    assert "not yet frozen" in row.info_label.get_label()


def test_dataset_row_exposes_dataset():
    dataset = FakeDataset(is_frozen=True)
    assert DtoolDatasetRow(dataset).dataset is dataset


def test_dataset_row_freeze_refreshes_markup():
    dataset = FakeDataset(is_frozen=False)
    row = DtoolDatasetRow(dataset)
    assert "* " in row.uuid_label.get_label()
    row.freeze()
    assert dataset.is_frozen is True
    assert "* " not in row.uuid_label.get_label()


def test_dataset_row_rebuild_clears_previous_contents():
    row = DtoolDatasetRow(FakeDataset(is_frozen=True))
    # Rebuilding must destroy the existing children before adding new ones.
    row._build()
    assert len(row.get_children()) == 1


# ===========================================================================
# DtoolBaseURIRow
# ===========================================================================

def test_base_uri_row_exposes_base_uri():
    base_uri = LocalBaseURIModel("/data/store")
    row = DtoolBaseURIRow(base_uri)
    assert row.base_uri is base_uri


def test_base_uri_row_builds_for_non_file_scheme_with_callbacks():
    calls = []
    row = DtoolBaseURIRow(
        S3BaseURIModel("bucket"),
        on_configure=lambda widget: calls.append("configure"),
        on_remove=lambda widget: calls.append("remove"),
        on_activate=lambda widget: calls.append("activate"),
    )
    assert row.base_uri.scheme == "s3"


def test_base_uri_row_exposes_info_label():
    row = DtoolBaseURIRow(LocalBaseURIModel("/data"))
    assert row.info_label.get_text() == "---"


def test_base_uri_row_spinner_start_stop_do_not_raise():
    row = DtoolBaseURIRow(LocalBaseURIModel("/data"))
    row.start_spinner()
    row.stop_spinner()


def test_base_uri_row_task_round_trip():
    # Regression: the task setter previously wrote to a misspelled attribute,
    # so the getter always returned None and the duplicate-task guard in the
    # main window never held.
    row = DtoolBaseURIRow(LocalBaseURIModel("/data"))
    assert row.task is None
    sentinel = object()
    row.task = sentinel
    assert row.task is sentinel
