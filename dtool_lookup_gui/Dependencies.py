#
# Copyright 2020 Lars Pastewka, Johannes Hoermann
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
import uuid

from .SimpleGraph import SimpleGraph

logger = logging.getLogger(__name__)


def _log_nested(log_func, dct):
    for l in json.dumps(dct, indent=2, default=str).splitlines():
        log_func(l)


def is_uuid(value):
    '''Check whether the data is a UUID.'''
    value = str(value)
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


class DependencyGraph:
    def __init__(self):
        self._reset_graph()

    def _reset_graph(self):
        self.graph = SimpleGraph()
        self.uuid_to_vertex = {}

    async def trace_dependencies(self, lookup, uuid, dependency_keys=None):
        """Build dependency graph by UUID."""
        self._reset_graph()

        if isinstance(dependency_keys, str):
            dependency_keys = json.loads(dependency_keys)

        if (dependency_keys is not None) and (not isinstance(dependency_keys, list)):
            logger.warn("Dependency keys not valid. Ignored.")
            dependency_keys = None

        datasets = await lookup.graph(uuid, dependency_keys)
        logger.debug(
            "Server response on querying dependency graph for UUID = {}.".format(
                uuid))
        _log_nested(logger.debug, datasets)

        for dataset in datasets:
            # this ceck should be redundant, as all documents have field 'uuid'
            # and this field is unique:
            if 'uuid' in dataset and dataset['uuid'] not in self.uuid_to_vertex:
                v = self.graph.add_vertex(
                    uuid=dataset['uuid'],
                    name=dataset['name'],
                    kind='root' if dataset['uuid'] == uuid else 'dependent')
                logger.debug("Create vertex {} for dataset '{}': '{}'".format(
                    v, dataset['uuid'], dataset['name']))
                self.uuid_to_vertex[dataset['uuid']] = v

        for dataset in datasets:
            if 'uuid' in dataset and 'derived_from' in dataset:
                for parent_uuid in dataset['derived_from']:
                    if is_uuid(parent_uuid):
                        if parent_uuid not in self.uuid_to_vertex:
                            v = self.graph.add_vertex(
                                uuid=parent_uuid,
                                name='Dataset does not exist in database.',
                                kind='does-not-exist')
                            logger.warning(
                                "Create vertex {} for missing parent dataset "
                                "'{}' of child '{}': '{}'".format(
                                    v, parent_uuid, dataset['uuid'],
                                    dataset['name']))
                            self.uuid_to_vertex[parent_uuid] = v

                        logger.debug(
                            "Create edge from child '{}':'{}' to parent "
                            "'{}'.".format(dataset['uuid'], dataset['name'],
                                           parent_uuid))
                        self.graph.add_edge(
                            self.uuid_to_vertex[dataset['uuid']],
                            self.uuid_to_vertex[parent_uuid])
                    else:
                        logger.warning(
                            "Parent dataset '{}' of child '{}': '{}' is no "
                            "valid UUID, ignored.".format(parent_uuid,
                                                          dataset['uuid'],
                                                          dataset['name']))
