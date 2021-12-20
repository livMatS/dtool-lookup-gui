#
# Copyright 2020-2021 Lars Pastewka
#           2020-2021 Johannes Hörmann
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

import json
import logging

from dtool_lookup_gui import is_uuid
from dtool_lookup_gui.models.simple_graph import SimpleGraph


logger = logging.getLogger(__name__)


def _log_nested(log_func, dct):
    for l in json.dumps(dct, indent=2, default=str).splitlines():
        log_func(l)


class DependencyGraph:
    def __init__(self):
        self._reset_graph()

    @property
    def graph(self):
        return self._graph

    def _reset_graph(self):
        self._graph = SimpleGraph()
        self._uuid_to_vertex = {}
        self._missing_uuids = []

    async def trace_dependencies(self, lookup, root_uuid, dependency_keys=None):
        """Build dependency graph by UUID."""
        self._reset_graph()

        if isinstance(dependency_keys, str):
            dependency_keys = json.loads(dependency_keys)

        if (dependency_keys is not None) and (not isinstance(dependency_keys, list)):
            logger.warning("Dependency keys not valid. Ignored.")
            dependency_keys = None

        datasets = await lookup.graph(root_uuid, dependency_keys)
        logger.debug("Server response on querying dependency graph for UUID = {}.".format(root_uuid))
        _log_nested(logger.debug, datasets)

        for dataset in datasets:
            # This check should be redundant, as all documents have field 'uuid'
            # and this field is unique:
            uuid = dataset['uuid']
            if 'uuid' in dataset and uuid not in self._uuid_to_vertex:
                v = self._graph.add_vertex(
                    uuid=uuid,
                    name=dataset['name'],
                    kind='root' if uuid == root_uuid else 'dependent')
                self._uuid_to_vertex[uuid] = v

        for dataset in datasets:
            if 'uuid' in dataset and 'derived_from' in dataset:
                for parent_uuid in dataset['derived_from']:
                    if is_uuid(parent_uuid):
                        if parent_uuid not in self._uuid_to_vertex:
                            # This UUID is present in the graph but not in the database
                            v = self._graph.add_vertex(
                                uuid=parent_uuid,
                                name='Dataset does not exist in database.',
                                kind='does-not-exist')
                            self._uuid_to_vertex[parent_uuid] = v
                            self._missing_uuids += [parent_uuid]

                        self._graph.add_edge(
                            self._uuid_to_vertex[dataset['uuid']],
                            self._uuid_to_vertex[parent_uuid])
                    else:
                        logger.warning(
                            "Parent dataset '{}' of child '{}': '{}' is no "
                            "valid UUID, ignored.".format(parent_uuid,
                                                          dataset['uuid'],
                                                          dataset['name']))

    @property
    def missing_uuids(self):
        return self._missing_uuids