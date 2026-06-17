"""TEMPORARY diagnostic: test the REAL failing operation (format-sniffing PNG
load via new_from_bytes/new_from_file) and report which libgdk_pixbuf is mapped.
Run under varying LD_LIBRARY_PATH / GDK_PIXBUF_MODULE_FILE to find why built-in
PNG sniffing fails in the frozen bundle. Delete before merge.
"""
import os
import struct
import zlib
import gi
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf, Gio, GLib  # noqa: E402


def _real_png_bytes():
    """Build a valid 1x1 RGBA PNG in-memory (correct CRCs)."""
    def chunk(typ, data):
        return (struct.pack(">I", len(data)) + typ + data
                + struct.pack(">I", zlib.crc32(typ + data) & 0xffffffff))
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
    raw = b"\x00\xff\x00\x00\xff"  # filter byte + RGBA pixel
    idat = chunk(b"IDAT", zlib.compress(raw))
    iend = chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


print("ENV GDK_PIXBUF_MODULE_FILE=", os.environ.get("GDK_PIXBUF_MODULE_FILE"))
print("ENV GDK_PIXBUF_MODULEDIR=", os.environ.get("GDK_PIXBUF_MODULEDIR"))
print("ENV LD_LIBRARY_PATH=", os.environ.get("LD_LIBRARY_PATH"))

# which libgdk_pixbuf is actually mapped into this process
try:
    with open("/proc/self/maps") as fh:
        libs = sorted({ln.split()[-1] for ln in fh
                       if "libgdk_pixbuf" in ln or "libpng16" in ln})
    print("MAPPED:", libs)
except Exception as e:
    print("MAPPED: err", e)

print("FORMATS:", sorted(f.get_name() for f in GdkPixbuf.Pixbuf.get_formats()))

png = _real_png_bytes()

# (1) explicit type loader (bypasses sniffing)
try:
    loader = GdkPixbuf.PixbufLoader.new_with_type("png")
    loader.write(png)
    loader.close()
    print("EXPLICIT_PNG: OK", loader.get_pixbuf().get_width(), "x",
          loader.get_pixbuf().get_height())
except Exception as e:
    print("EXPLICIT_PNG: FAIL:", repr(e))

# (2) sniffing loader (no type) -- this is the path GTK uses for image-missing
try:
    loader = GdkPixbuf.PixbufLoader()
    loader.write(png)
    loader.close()
    print("SNIFF_PNG: OK", loader.get_pixbuf().get_width())
except Exception as e:
    print("SNIFF_PNG: FAIL:", repr(e))

# (3) new_from_stream (sniffing) -- closest to GTK's GResource load
try:
    stream = Gio.MemoryInputStream.new_from_bytes(GLib.Bytes.new(png))
    pb = GdkPixbuf.Pixbuf.new_from_stream(stream, None)
    print("STREAM_PNG: OK", pb.get_width())
except Exception as e:
    print("STREAM_PNG: FAIL:", repr(e))
