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
"""Unit tests for the pure helper modules in dtool_lookup_gui.utils.

These have no GTK dependency, so they run without the application fixtures.
"""
import datetime
import os

import pytest

from dtool_lookup_gui.utils import query as query_utils
from dtool_lookup_gui.utils.environ import TemporaryOSEnviron
from dtool_lookup_gui.utils import date as date_utils


# ---------------------------------------------------------------------------
# utils.query
# ---------------------------------------------------------------------------

def test_load_query_text_parses_json():
    assert query_utils.load_query_text('{"a": 1}') == {"a": 1}


def test_dump_single_line_query_text_has_no_newlines():
    out = query_utils.dump_single_line_query_text({"a": 1, "b": 2})
    assert "\n" not in out
    assert query_utils.load_query_text(out) == {"a": 1, "b": 2}


def test_dump_multi_line_query_text_is_indented():
    out = query_utils.dump_multi_line_query_text({"a": 1})
    assert "\n" in out
    assert query_utils.load_query_text(out) == {"a": 1}


def test_single_line_sanitize_round_trips():
    assert query_utils.single_line_sanitize_query_text('{ "a" : 1 }') == '{"a": 1}'


def test_multi_line_sanitize_round_trips():
    out = query_utils.multi_line_sanitize_query_text('{"a": 1}')
    assert query_utils.load_query_text(out) == {"a": 1}
    assert "\n" in out


@pytest.mark.parametrize("text,expected", [
    ('{"a": 1}', True),
    ('[1, 2, 3]', True),
    ('not json', False),
    ('{"a": }', False),
    ('', False),
])
def test_is_valid_query(text, expected):
    assert query_utils.is_valid_query(text) is expected


# ---------------------------------------------------------------------------
# utils.environ.TemporaryOSEnviron
# ---------------------------------------------------------------------------

def test_temporary_os_environ_injects_and_restores():
    key = "DTOOL_LOOKUP_GUI_TEST_VAR"
    assert key not in os.environ
    with TemporaryOSEnviron(env={key: "value"}):
        assert os.environ[key] == "value"
    assert key not in os.environ


def test_temporary_os_environ_casts_values_to_str():
    key = "DTOOL_LOOKUP_GUI_TEST_INT"
    with TemporaryOSEnviron(env={key: 42}):
        assert os.environ[key] == "42"
    assert key not in os.environ


def test_temporary_os_environ_restores_overwritten_value():
    key = "DTOOL_LOOKUP_GUI_TEST_EXISTING"
    os.environ[key] = "original"
    try:
        with TemporaryOSEnviron(env={key: "overwritten"}):
            assert os.environ[key] == "overwritten"
        assert os.environ[key] == "original"
    finally:
        del os.environ[key]


def test_temporary_os_environ_restores_on_exception():
    key = "DTOOL_LOOKUP_GUI_TEST_EXC"
    with pytest.raises(RuntimeError):
        with TemporaryOSEnviron(env={key: "value"}):
            assert os.environ[key] == "value"
            raise RuntimeError("boom")
    assert key not in os.environ


def test_temporary_os_environ_none_is_noop():
    before = dict(os.environ)
    with TemporaryOSEnviron():
        pass
    assert dict(os.environ) == before


# ---------------------------------------------------------------------------
# utils.date
# ---------------------------------------------------------------------------

def test_to_timestamp_passes_through_numeric():
    assert date_utils.to_timestamp(1234567890) == 1234567890
    assert date_utils.to_timestamp(12.5) == 12.5


def test_to_timestamp_parses_rfc_string():
    ts = date_utils.to_timestamp("Mon, 07 Dec 2021 09:00:00 GMT")
    assert isinstance(ts, (int, float))
    assert ts > 0


def test_to_timestamp_invalid_string_returns_minus_one():
    assert date_utils.to_timestamp("not a date") == -1


def test_date_to_string_returns_date():
    d = date_utils.date_to_string(1234567890)
    assert isinstance(d, datetime.date)


def test_time_locale_restores_previous_locale():
    import locale
    saved = locale.setlocale(locale.LC_TIME)
    with date_utils.time_locale("C"):
        pass
    assert locale.setlocale(locale.LC_TIME) == saved


# ---------------------------------------------------------------------------
# utils.subprocess.launch_default_app_for_uri
# ---------------------------------------------------------------------------

def test_launch_default_app_for_uri_linux_uses_xdg_open():
    from unittest.mock import patch
    from dtool_lookup_gui.utils import subprocess as sp
    with patch.object(sp.platform, "system", return_value="Linux"), \
            patch.object(sp.subprocess, "call") as mock_call:
        sp.launch_default_app_for_uri("file:///tmp/example.txt")
    mock_call.assert_called_once_with(("xdg-open", "/tmp/example.txt"))


def test_launch_default_app_for_uri_macos_uses_open():
    from unittest.mock import patch
    from dtool_lookup_gui.utils import subprocess as sp
    with patch.object(sp.platform, "system", return_value="Darwin"), \
            patch.object(sp.subprocess, "call") as mock_call:
        sp.launch_default_app_for_uri("file:///tmp/example.txt")
    mock_call.assert_called_once_with(("open", "/tmp/example.txt"))


def test_launch_default_app_for_uri_warns_on_non_file_scheme(caplog):
    import logging
    from unittest.mock import patch
    from dtool_lookup_gui.utils import subprocess as sp
    with patch.object(sp.platform, "system", return_value="Linux"), \
            patch.object(sp.subprocess, "call"):
        with caplog.at_level(logging.WARNING, logger="dtool_lookup_gui.utils.subprocess"):
            sp.launch_default_app_for_uri("http://example.com/x")
    assert any("not supported" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# utils.logging
# ---------------------------------------------------------------------------

def test_log_nested_emits_one_call_per_line():
    from dtool_lookup_gui.utils.logging import _log_nested
    lines = []
    _log_nested(lines.append, {"a": 1, "b": {"c": 2}})
    assert lines, "expected at least one logged line"
    assert any('"a"' in line for line in lines)


def test_default_filter_excludes_known_noise():
    import logging
    from dtool_lookup_gui.utils.logging import DefaultFilter
    f = DefaultFilter()
    noisy = logging.LogRecord("n", logging.ERROR, __file__, 1,
                              "Unclosed client session", None, None)
    normal = logging.LogRecord("n", logging.INFO, __file__, 1,
                               "a perfectly ordinary message", None, None)
    assert f.filter(noisy) is False
    assert f.filter(normal) is True
