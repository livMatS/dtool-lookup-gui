"""Runtime hook: configure GdkPixbuf to use bundled loaders.

The PyInstaller spec bundles:
  - GdkPixbuf loader .so files  → lib/gdk-pixbuf/loaders/
  - loaders.cache               → lib/gdk-pixbuf/loaders.cache
    (with @executable_path/lib/gdk-pixbuf/loaders as path prefix)

At runtime we rewrite @executable_path → sys._MEIPASS and point
GDK_PIXBUF_MODULE_FILE at the rewritten cache so GdkPixbuf finds
the bundled PNG/JPEG/etc. loaders instead of (absent) system ones.
"""
import os
import sys
import tempfile

_meipass = sys._MEIPASS
_cache_src = os.path.join(_meipass, 'lib', 'gdk-pixbuf', 'loaders.cache')
_loaders_dir = os.path.join(_meipass, 'lib', 'gdk-pixbuf', 'loaders')

if os.path.isfile(_cache_src):
    with open(_cache_src, 'rb') as _f:
        _data = _f.read()
    # Replace the @executable_path placeholder written by the spec
    _data = _data.replace(b'@executable_path', _meipass.encode())
    # Write rewritten cache to a temp file (cache src is read-only inside bundle)
    _fd, _tmp_cache = tempfile.mkstemp(prefix='gdkpixbuf-', suffix='.cache')
    try:
        os.write(_fd, _data)
    finally:
        os.close(_fd)
    os.environ['GDK_PIXBUF_MODULE_FILE'] = _tmp_cache

# Also point the module dir directly (belt-and-suspenders)
if os.path.isdir(_loaders_dir):
    os.environ['GDK_PIXBUF_MODULEDIR'] = _loaders_dir
