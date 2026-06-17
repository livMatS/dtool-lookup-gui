#
# Copyright 2021-2022 Johannes Laurin Hörmann
#           2020-2021 Lars Pastewka
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

# see https://docs.python.org/3/library/multiprocessing.html#multiprocessing.freeze_support
import multiprocessing

if __name__ == '__main__':
    multiprocessing.freeze_support()

    # TEMPORARY frozen-runtime diagnostic (revert before merge): when
    # DTOOL_GUI_DIAG is set, report GdkPixbuf state from INSIDE the frozen
    # interpreter (after all PyInstaller rthooks have run) and exit.
    import os as _os
    if _os.environ.get("DTOOL_GUI_DIAG"):
        import sys as _sys
        # Fix-test override applied BEFORE first GdkPixbuf use (after rthooks ran):
        #   DTOOL_GUI_DIAG_CACHE=UNSET   -> remove GDK_PIXBUF_MODULE_FILE
        #   DTOOL_GUI_DIAG_CACHE=<path>  -> set it to <path>
        _ov = _os.environ.get("DTOOL_GUI_DIAG_CACHE")
        if _ov == "UNSET":
            _os.environ.pop("GDK_PIXBUF_MODULE_FILE", None)
        elif _ov:
            _os.environ["GDK_PIXBUF_MODULE_FILE"] = _ov
        print("DIAG GDK_PIXBUF_MODULE_FILE=", _os.environ.get("GDK_PIXBUF_MODULE_FILE"))
        print("DIAG GDK_PIXBUF_MODULEDIR=", _os.environ.get("GDK_PIXBUF_MODULEDIR"))
        print("DIAG cache exists=",
              _os.path.exists(_os.environ.get("GDK_PIXBUF_MODULE_FILE") or ""))
        try:
            with open("/proc/self/maps") as _fh:
                _libs = sorted({ln.split()[-1] for ln in _fh
                                if "libgdk_pixbuf" in ln or "libpng16" in ln})
            print("DIAG MAPPED:", _libs)
        except Exception as _e:
            print("DIAG MAPPED err", _e)
        import gi as _gi
        _gi.require_version("GdkPixbuf", "2.0")
        from gi.repository import GdkPixbuf as _GP
        print("DIAG FORMATS:", sorted(f.get_name() for f in _GP.Pixbuf.get_formats()))
        import struct as _st, zlib as _zl

        def _chunk(t, d):
            return (_st.pack(">I", len(d)) + t + d
                    + _st.pack(">I", _zl.crc32(t + d) & 0xffffffff))
        _png = (b"\x89PNG\r\n\x1a\n"
                + _chunk(b"IHDR", _st.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
                + _chunk(b"IDAT", _zl.compress(b"\x00\xff\x00\x00\xff"))
                + _chunk(b"IEND", b""))
        try:
            _l = _GP.PixbufLoader()
            _l.write(_png)
            _l.close()
            print("DIAG SNIFF_PNG: OK", _l.get_pixbuf().get_width())
        except Exception as _e:
            print("DIAG SNIFF_PNG: FAIL:", repr(_e))
        try:
            with open("/proc/self/maps") as _fh:
                _libs2 = sorted({ln.split()[-1] for ln in _fh
                                 if "libgdk_pixbuf" in ln})
            print("DIAG MAPPED_AFTER:", _libs2)
        except Exception as _e:
            print("DIAG MAPPED_AFTER err", _e)
        _sys.stdout.flush()
        _sys.exit(0)

    from dtool_lookup_gui.main import run_gui
    run_gui()
