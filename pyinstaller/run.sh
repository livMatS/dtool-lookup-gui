#!/bin/bash
(cd dtool_lookup_gui && glib-compile-schemas .)
pyinstaller -y ./pyinstaller/dtool-lookup-gui.spec
