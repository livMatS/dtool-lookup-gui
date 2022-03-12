#!/bin/bash
#
# Place link to desktop launcher within appropriate place below home folder
#
APPDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
mkdir -p "${HOME}/.local/share/applications"
ln -sf "${APPDIR}/etc/dtool-lookup-gui.desktop" "${HOME}/.local/share/applications/dtool-lookup-gui.desktop"
