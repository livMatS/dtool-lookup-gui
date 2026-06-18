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
"""Unit tests for the data-model layer (models.base_uris and models.datasets).

These exercise the base-URI registry and DatasetModel against real on-disk
dtool datasets (the local_dataset_uri fixture) and isolated GSettings / dtool
config (set up in test/conftest.py). The lookup-server API is never contacted:
the cached code paths are tested directly and the one remote helper is
monkeypatched.
"""
import os

import pytest

import dtoolcore
from dtoolcore.utils import generous_parse_uri, write_config_value_to_file

from dtool_lookup_gui.models.settings import settings
from dtool_lookup_gui.models import base_uris as base_uris_module
from dtool_lookup_gui.models.base_uris import (
    LocalBaseURIModel,
    S3BaseURIModel,
    SMBBaseURIModel,
    LookupBaseURIModel,
)
from dtool_lookup_gui.models.datasets import (
    DatasetModel,
    _info,
    _load_dataset,
    _list_datasets,
    _list_proto_datasets,
    _mangle_lookup_manifest,
    _lookup_info,
)


@pytest.fixture
def clean_local_base_uris():
    """Ensure each test starts and ends with an empty local base-URI list."""
    settings.local_base_uris = []
    yield
    settings.local_base_uris = []


def _expected_path(path):
    return generous_parse_uri(path).path


# ===========================================================================
# models.base_uris
# ===========================================================================

# --- BaseURI / scheme behaviour -------------------------------------------

def test_base_uri_str_and_properties():
    u = LocalBaseURIModel("/data/foo")
    assert u.scheme == "file"
    assert u.uri_name == "/data/foo"
    assert str(u) == "file:///data/foo"


def test_base_uri_equality():
    assert LocalBaseURIModel("/a") == LocalBaseURIModel("/a")
    assert LocalBaseURIModel("/a") != LocalBaseURIModel("/b")


def test_base_uri_editable_flag():
    # 'file' is editable, 's3' is in NON_EDITABLE_SCHEMES.
    assert LocalBaseURIModel("/a").editable is True
    assert S3BaseURIModel("bucket").editable is False


# --- LocalBaseURIModel registry -------------------------------------------

def test_local_add_directory_registers(clean_local_base_uris, tmp_path):
    LocalBaseURIModel.add_directory(str(tmp_path))
    assert _expected_path(str(tmp_path)) in settings.local_base_uris


def test_local_add_directory_rejects_non_file_scheme(clean_local_base_uris):
    with pytest.raises(ValueError):
        LocalBaseURIModel.add_directory("s3://bucket")


def test_local_add_directory_rejects_duplicate(clean_local_base_uris, tmp_path):
    LocalBaseURIModel.add_directory(str(tmp_path))
    with pytest.raises(ValueError):
        LocalBaseURIModel.add_directory(str(tmp_path))


def test_local_all_returns_models(clean_local_base_uris, tmp_path):
    LocalBaseURIModel.add_directory(str(tmp_path))
    models = LocalBaseURIModel.all()
    assert [m.uri_name for m in models] == [_expected_path(str(tmp_path))]
    assert all(isinstance(m, LocalBaseURIModel) for m in models)


def test_local_remove(clean_local_base_uris, tmp_path):
    LocalBaseURIModel.add_directory(str(tmp_path))
    (model,) = LocalBaseURIModel.all()
    LocalBaseURIModel.remove(model)
    assert _expected_path(str(tmp_path)) not in settings.local_base_uris


def test_local_create_dataset(clean_local_base_uris, tmp_path):
    base = LocalBaseURIModel(str(tmp_path))
    ds = base.create_dataset("my_dataset")
    assert isinstance(ds, DatasetModel)
    assert ds.name == "my_dataset"
    assert ds.is_frozen is False


def test_local_create_dataset_invalid_name(clean_local_base_uris, tmp_path):
    base = LocalBaseURIModel(str(tmp_path))
    with pytest.raises(ValueError):
        base.create_dataset("invalid/name!")


# --- config-file backed base URIs -----------------------------------------

def test_s3_all_discovers_configured_endpoints():
    write_config_value_to_file("DTOOL_S3_ENDPOINT_mybucket", "https://s3.example.com")
    names = [m.uri_name for m in S3BaseURIModel.all()]
    assert "mybucket" in names


def test_smb_all_discovers_configured_servers():
    write_config_value_to_file("DTOOL_SMB_SERVER_NAME_myserver", "fileserver")
    names = [m.uri_name for m in SMBBaseURIModel.all()]
    assert "myserver" in names


# --- LookupBaseURIModel ----------------------------------------------------

def test_lookup_base_uri_parses_uri():
    m = LookupBaseURIModel("s3://my-bucket")
    assert m.scheme == "s3"
    assert m.uri_name == "my-bucket"


# --- top-level discovery ---------------------------------------------------

@pytest.mark.asyncio
async def test_all_local_only(clean_local_base_uris, tmp_path):
    LocalBaseURIModel.add_directory(str(tmp_path))
    result = await base_uris_module.all(local=True, lookup=None)
    names = [b.uri_name for b in result]
    assert _expected_path(str(tmp_path)) in names


@pytest.mark.asyncio
async def test_all_includes_lookup_base_uris(clean_local_base_uris, monkeypatch):
    async def fake_all(username):
        return [LookupBaseURIModel("s3://remote-bucket")]

    monkeypatch.setattr(LookupBaseURIModel, "all", fake_all)
    result = await base_uris_module.all(local=False, lookup="testuser")
    assert any(b.uri_name == "remote-bucket" for b in result)


# ===========================================================================
# models.datasets
# ===========================================================================

# --- module-level helpers --------------------------------------------------

def test_load_dataset_returns_frozen_dataset(local_dataset_uri):
    ds = _load_dataset(local_dataset_uri)
    assert isinstance(ds, dtoolcore.DataSet)


def test_info_for_frozen_dataset(local_dataset_uri):
    info = _info(_load_dataset(local_dataset_uri))
    assert info["is_frozen"] is True
    assert info["type"] == "dtool-dataset"
    assert info["name"] == "test_dataset"
    assert info["scheme"] == "file"
    # The fixture stores two items.
    assert len(info["manifest"]) == 2
    assert info["tags"] == []
    assert info["annotations"] == {}


def test_list_datasets_and_proto(local_dataset_uri):
    base_uri = os.path.dirname(_expected_path(local_dataset_uri))
    frozen = _list_datasets(base_uri)
    proto = _list_proto_datasets(base_uri)
    assert len(frozen) == 1
    assert isinstance(frozen[0], DatasetModel)
    assert proto == []


def test_mangle_lookup_manifest():
    out = _mangle_lookup_manifest(
        {"items": {"id1": {"name": "a"}, "id2": {"name": "b"}}})
    assert ("id1", {"name": "a"}) in out
    assert len(out) == 2


@pytest.mark.asyncio
async def test_lookup_info_with_size():
    info = await _lookup_info({
        "uri": "s3://bucket/uuid",
        "uuid": "u",
        "size_in_bytes": 19347,
        "creator_username": "alice",
        "name": "ds",
        "frozen_at": 1683797362.855,
    })
    assert info["type"] == "lookup"
    assert info["scheme"] == "s3"
    assert info["base_uri"] == "bucket"
    assert info["size_int"] == 19347
    assert info["size_str"] != "unknown"
    assert info["is_frozen"] is True


@pytest.mark.asyncio
async def test_lookup_info_without_size_is_unknown():
    info = await _lookup_info({
        "uri": "s3://bucket/uuid",
        "uuid": "u",
        "creator_username": "alice",
        "name": "ds",
        "frozen_at": 1683797362.855,
    })
    assert info["size_int"] is None
    assert info["size_str"] == "unknown"


# --- DatasetModel construction / attribute access --------------------------

def test_dataset_model_from_uri_attribute_access(local_dataset_uri):
    m = DatasetModel.from_uri(local_dataset_uri)
    assert str(m) == m.uri
    assert m.is_frozen is True
    assert m.name == "test_dataset"


def test_dataset_model_from_dataset(local_dataset_uri):
    m = DatasetModel.from_dataset(_load_dataset(local_dataset_uri))
    assert m.name == "test_dataset"


def test_dataset_model_requires_uri_or_info():
    with pytest.raises(ValueError):
        DatasetModel()


def test_dataset_model_setattr_updates_info(local_dataset_uri):
    m = DatasetModel.from_uri(local_dataset_uri)
    m.custom_field = "x"
    assert m._dataset_info["custom_field"] == "x"
    assert m.custom_field == "x"


def test_dataset_model_getstate_setstate_roundtrip(local_dataset_uri):
    m = DatasetModel.from_uri(local_dataset_uri)
    state = m.__getstate__()
    other = DatasetModel.from_uri(local_dataset_uri)
    other.__setstate__(state)
    assert other._dataset_info == state


@pytest.mark.asyncio
async def test_dataset_model_from_lookup():
    m = await DatasetModel.from_lookup({
        "uri": "s3://bucket/uuid",
        "uuid": "u",
        "size_in_bytes": 10,
        "creator_username": "alice",
        "name": "remote_ds",
        "frozen_at": 1683797362.855,
    })
    assert m.name == "remote_ds"
    assert m.is_frozen is True


# --- DatasetModel mutation against a real dataset --------------------------

def test_dataset_model_put_and_delete_tag(local_dataset_uri):
    m = DatasetModel.from_uri(local_dataset_uri)
    m.put_tag("alpha")
    assert "alpha" in m.tags
    m.delete_tag("alpha")
    assert "alpha" not in m.tags


def test_dataset_model_put_and_delete_annotation(local_dataset_uri):
    m = DatasetModel.from_uri(local_dataset_uri)
    m.put_annotation("key", "value")
    assert m.annotations["key"] == "value"
    m.delete_annotation("key")
    assert "key" not in m.annotations


def test_dataset_model_put_readme(local_dataset_uri):
    m = DatasetModel.from_uri(local_dataset_uri)
    m.put_readme("desc: hello\n")
    assert m.readme_content == "desc: hello\n"


def test_dataset_model_freeze(clean_local_base_uris, tmp_path):
    base = LocalBaseURIModel(str(tmp_path))
    m = base.create_dataset("to_freeze")
    assert m.is_frozen is False
    m.freeze()
    assert m.is_frozen is True


# --- DatasetModel cached lookups (no server contact) -----------------------

@pytest.mark.asyncio
async def test_get_readme_returns_cached_content(local_dataset_uri):
    m = DatasetModel.from_uri(local_dataset_uri)
    m._dataset_info["readme_content"] = "desc: cached\n"
    assert await m.get_readme() == "desc: cached\n"


@pytest.mark.asyncio
async def test_get_manifest_returns_cached_for_frozen(local_dataset_uri):
    m = DatasetModel.from_uri(local_dataset_uri)
    manifest = await m.get_manifest()
    assert manifest == m._dataset_info["manifest"]
    assert len(manifest) == 2


@pytest.mark.asyncio
async def test_get_manifest_empty_for_proto(clean_local_base_uris, tmp_path):
    m = LocalBaseURIModel(str(tmp_path)).create_dataset("proto_ds")
    assert m.is_frozen is False
    assert await m.get_manifest() == {}


@pytest.mark.asyncio
async def test_get_tags_returns_cached(local_dataset_uri):
    m = DatasetModel.from_uri(local_dataset_uri)
    assert await m.get_tags() == m._dataset_info["tags"]


@pytest.mark.asyncio
async def test_get_annotations_returns_cached(local_dataset_uri):
    m = DatasetModel.from_uri(local_dataset_uri)
    assert await m.get_annotations() == m._dataset_info["annotations"]


# --- DatasetModel.get_item -------------------------------------------------

@pytest.mark.asyncio
async def test_get_item_returns_existing_path(local_dataset_uri):
    m = DatasetModel.from_uri(local_dataset_uri)
    item_uuid = list(_load_dataset(local_dataset_uri).identifiers)[0]
    path = await m.get_item(item_uuid)
    assert os.path.exists(path)


@pytest.mark.asyncio
async def test_get_item_unknown_uuid_raises(local_dataset_uri):
    m = DatasetModel.from_uri(local_dataset_uri)
    with pytest.raises(ValueError):
        await m.get_item("nonexistent-uuid")
