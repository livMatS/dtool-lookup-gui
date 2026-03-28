import os, sys

loaders_dir = os.path.join(sys._MEIPASS, "gdk_pixbuf_loaders")
cache_file = os.path.join(loaders_dir, "loaders.cache")

if os.path.isdir(loaders_dir):
    os.environ["GDK_PIXBUF_MODULEDIR"] = loaders_dir
if os.path.isfile(cache_file):
    os.environ["GDK_PIXBUF_MODULE_FILE"] = cache_file
