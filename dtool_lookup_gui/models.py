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
import os

import dtoolcore

from dtool_gui_tk.models import (
    LocalBaseURIModel,
    DataSetListModel,
    DataSetModel,
    ProtoDataSetModel,
    MetadataSchemaListModel,
    UnsupportedTypeError,
)


class BaseURIModel():
    "Model for managing base URI."

    def __init__(self, base_uri=os.path.curdir):
        self.put_base_uri(base_uri)

    def get_base_uri(self):
        """Return the base URI.

        :returns: base URI where datasets will be read from and written to
        """
        return self._base_uri

    def put_base_uri(self, base_uri):
        """Put/update the base URI.

        :param base_uri: base URI
        """
        value = dtoolcore.utils.sanitise_uri(base_uri)
        self._base_uri = value
