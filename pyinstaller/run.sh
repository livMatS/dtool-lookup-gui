#!/bin/bash
(cd dtool_lookup_gui && glib-compile-schemas .)
pyinstaller -y --clean pyinstaller/dtool-lookup-gui.spec
