"""
Runtime hook: fix gdk-pixbuf loaders path resolution inside PyInstaller bundle.

The loaders.cache bundled at build time contains relative paths like:
  "gdk_pixbuf_loaders/libpixbufloader-png.so"

gdk-pixbuf requires absolute paths, so we rewrite the cache to a temp file
with sys._MEIPASS-prefixed absolute paths, then point GDK_PIXBUF_MODULE_FILE
at that temp file.

This runs after PyInstaller's own pyi_rth_gdkpixbuf.py, overriding whatever
it set (which would point to a non-existent path anyway).
"""
import os
import sys
import tempfile

loaders_dir = os.path.join(sys._MEIPASS, "gdk_pixbuf_loaders")
bundled_cache = os.path.join(loaders_dir, "loaders.cache")

if os.path.isdir(loaders_dir):
    os.environ["GDK_PIXBUF_MODULEDIR"] = loaders_dir

    if os.path.isfile(bundled_cache):
        # Rewrite relative paths to absolute paths for this runtime instance.
        # Build-time cache has lines like: "gdk_pixbuf_loaders/libpixbufloader-png.so"
        # Runtime needs:                   "/tmp/_MEIxxxxxx/gdk_pixbuf_loaders/libpixbufloader-png.so"
        with open(bundled_cache, "r") as f:
            content = f.read()

        content = content.replace(
            '"gdk_pixbuf_loaders/',
            '"' + loaders_dir + '/'
        )

        fd, tmp_cache = tempfile.mkstemp(suffix="_loaders.cache")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(content)
            os.environ["GDK_PIXBUF_MODULE_FILE"] = tmp_cache
        except Exception:
            try:
                os.unlink(tmp_cache)
            except OSError:
                pass
