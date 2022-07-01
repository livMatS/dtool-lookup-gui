#!/bin/bash -e
#
# Run this to update the launcher file with the current path to the application icon
#

APPDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ -w "$APPDIR"/dtool-lookup-gui.desktop ]; then
	sed -i -e "s@^Icon=.*@Icon=$APPDIR/dtool_logo.png@" "$APPDIR"/dtool-lookup-gui.desktop
else
	echo "$APPDIR"/dtool-lookup-gui.desktop is not writable
	exit 1
fi
