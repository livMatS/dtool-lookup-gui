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

import uuid

from .SimpleGraph import SimpleGraph


def is_uuid(value):
    '''Check whether the data is a UUID.'''
    value = str(value)
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


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


class DependencyGraph:
    def __init__(self):
        self._reset_graph()

    def _reset_graph(self):
        self.graph = SimpleGraph()
        self.uuid_to_vertex = {}

    async def _trace_parents(self, lookup, parent_uuid):
        datasets = await lookup.by_uuid(parent_uuid)
        if len(datasets) == 0:
            # This UUID does not exist in the database
            print(f'trace: UUID {parent_uuid} does not exist')
            v = self.graph.add_vertex(
                uuid=parent_uuid,
                name='Dataset does not exist in database.')
        else:
            # There may be the same dataset in multiple storage locations,
            # we just use the first
            dataset = datasets[0]
            v = self.graph.add_vertex(uuid=parent_uuid, name=dataset['name'])
            visited_uuids = set([])
            readme = await lookup.readme(dataset['uri'])
            uuids_in_readme = enumerate_uuids(readme)
            for path, parent_uuid in uuids_in_readme:
                if parent_uuid not in visited_uuids:
                    if parent_uuid in self.uuid_to_vertex:
                        # We have a Vertex for this UUID, simple add an
                        # edge
                        self.graph.add_edge(self.uuid_to_vertex[parent_uuid], v)
                    else:
                        # Create a new Vertex and continue tracing
                        visited_uuids.add(parent_uuid)
                        self.uuid_to_vertex[parent_uuid] = None
                        print('trace parent:', dataset['uuid'], '<-',
                              parent_uuid, 'via README entry', path)
                        v2 = await self._trace_parents(lookup, parent_uuid)
                        self.uuid_to_vertex[parent_uuid] = v2
                        self.graph.add_edge(v2, v)
        return v

    async def _trace_children(self, lookup, parent_uuid, v=None):
        if v is None:
            v = self.graph.add_vertex()
            self.uuid[v] = parent_uuid
        datasets = await lookup.search(parent_uuid)
        for dataset in datasets:
            readme = await lookup.readme(dataset['uri'])
            uuids_in_readme = enumerate_uuids(readme)
            print(parent_uuid, dataset['uuid'])
            print(readme)
            print(uuids_in_readme)
            if parent_uuid in [x[1] for x in uuids_in_readme]:
                if parent_uuid in self.uuid_to_vertex:
                    # We have a Vertex for this UUID, simple add an edge
                    print('trace child:', parent_uuid, '<-', dataset['uuid'],
                          '(vertex already existed)')
                    self.graph.add_edge(v, self.uuid_to_vertex[parent_uuid])
                else:
                    # Create a new Vertex and continue tracing
                    self.uuid_to_vertex[parent_uuid] = None
                    print('trace child:', parent_uuid, '<-', dataset['uuid'],
                          '(new vertex)')
                    v2 = await self._trace_children(lookup, dataset['uuid'])
                    self.name[v2] = dataset['name']
                    self.uuid_to_vertex[parent_uuid] = v2
                    self.graph.add_edge(v, v2)
        return v

    async def trace_dependencies(self, lookup, uuid):
        self._reset_graph()
        root_vertex = await self._trace_parents(lookup, uuid)
        await self._trace_children(lookup, uuid, root_vertex)
