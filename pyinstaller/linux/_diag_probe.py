"""TEMPORARY diagnostic: report GdkPixbuf formats + attempt a PNG load.
Run under varying LD_LIBRARY_PATH / GDK_PIXBUF_MODULE_FILE to find which
bundled lib breaks PNG decoding. Delete before merge.
"""
import base64
import gi
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf  # noqa: E402

print("FORMATS:", sorted(f.get_name() for f in GdkPixbuf.Pixbuf.get_formats()))
_png = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR4nGNgAAIAAAUAAen63NgAAAAASUVORK5CYII="
)
try:
    _l = GdkPixbuf.PixbufLoader.new_with_type("png")
    _l.write(_png)
    _l.close()
    print("PNG_LOAD: OK")
except Exception as e:
    print("PNG_LOAD: FAIL:", repr(e))
