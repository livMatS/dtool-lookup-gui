#
# Copyright 2021 Johannes Hörmann
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


def load_query_text(text):
    return json.loads(text)


def dump_single_line_query_text(query):
    return json.dumps(query)


def dump_multi_line_query_text(query):
    return json.dumps(query, indent=4)


def single_line_sanitize_query_text(text):
    """Formats a query text coherently."""
    return dump_single_line_query_text(load_query_text(text))


def multi_line_sanitize_query_text(text):
    """Formats a query text coherently."""
    return dump_multi_line_query_text(load_query_text(text))


def is_valid_query(text):
    try:
        load_query_text(text)
    except:
        return False
    return True
