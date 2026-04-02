#!/usr/bin/env python3
"""Collect GdkPixbuf runtime deps (libpng, libjpeg) via ldd and write to pixbuf_deps.txt.

Run from the repository root. Writes pyinstaller/linux/pixbuf_deps.txt with one
resolved .so path per line. The PyInstaller spec reads this file to explicitly
bundle the libs that GdkPixbuf needs for built-in PNG/JPEG decoding.
"""
import subprocess
import os
import re
import sys

so_files = subprocess.run(
    ['find', '/lib', '/usr/lib', '-name', 'libgdk_pixbuf-2.0.so.0.*', '-not', '-type', 'l'],
    capture_output=True, text=True
).stdout.strip().split('\n')
so_files = [s for s in so_files if s]

if not so_files:
    print('WARNING: libgdk_pixbuf-2.0.so.0.* not found', file=sys.stderr)
    sys.exit(0)

print(f'Found libgdk_pixbuf: {so_files}')

deps = []
for lib in so_files:
    out = subprocess.run(['ldd', lib], capture_output=True, text=True).stdout
    for line in out.splitlines():
        m = re.search(r'(libpng\S+|libjpeg\S+)\s+=>\s+(\S+)', line)
        if m:
            path = m.group(2)
            if os.path.isfile(path) and path not in deps:
                deps.append(path)
                print(f'Found dep: {path}')

out_path = os.path.join(os.path.dirname(__file__), 'pixbuf_deps.txt')
with open(out_path, 'w') as f:
    f.write('\n'.join(deps) + '\n')
print(f'Written {len(deps)} deps to {out_path}')
