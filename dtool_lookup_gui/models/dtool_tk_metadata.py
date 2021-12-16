#
# Copyright 2021 Lars Pastewka
#           2021 Johannes Hörmann
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
"""Module for working with metadata schemas.
Example usage:
>>> from metadata import MetadataSchemaItem
>>> nucl_acid = MetadataSchemaItem({"type": "string", "enum": ["DNA", "RNA"]})
>>> nucl_acid.type
'string'
>>> nucl_acid.enum
['DNA', 'RNA']
>>> print(nucl_acid.is_okay("RNA"))
True
>>> print(nucl_acid.is_okay("Not DNA"))
False
>>> for i in nucl_acid.issues("Not DNA"):
...     print(i)
...
'Not DNA' is not one of ['DNA', 'RNA']
"""

import jsonschema
import jsonschema.exceptions
import jsonschema.validators


class SchemaError(jsonschema.exceptions.SchemaError):
    pass


class MetadataSchemaItem(object):

    def __init__(self, schema):
        self._schema = schema
        self._ivalidator = jsonschema.validators.Draft7Validator(schema)

        # Ensure that the schema is valid.
        try:
            self._ivalidator.check_schema(self._schema)
        except jsonschema.exceptions.SchemaError as e:
            raise(SchemaError(e.message))

    def __eq__(self, other):
        return self._schema == other._schema

    def __repr__(self):
        return "<{}({}) at {}>".format(
            self.__class__.__name__, self._schema,
            hex(id(self)))

    @property
    def type(self):
        return self._schema["type"]

    @property
    def enum(self):
        return self._schema.get("enum", None)

    @property
    def schema(self):
        return self._schema

    def is_okay(self, value):
        return self._ivalidator.is_valid(value)

    def issues(self, value):
        return [i.message for i in self._ivalidator.iter_errors(value)]
