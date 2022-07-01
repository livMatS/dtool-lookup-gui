#!/bin/bash
#
# Place link to desktop launcher within appropriate place below home folder
# Expects dtool-lookup-gui executable to reside within same directory as this script.
# Expects dtool-lookup-gui.desktop launcher to reside within same directory as this script.
#
APPDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
mkdir -p "${HOME}/.local/share/applications"
ln -sf "${APPDIR}/dtool-lookup-gui.desktop" "${HOME}/.local/share/applications/dtool-lookup-gui.desktop"
