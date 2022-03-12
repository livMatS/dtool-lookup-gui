#!/bin/bash -e

#
# Run this to update the launcher file with the current path to the application icon
#

APPDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
if [ -w "$APPDIR"/etc/dtool-lookup-gui.desktop ]; then
	sed -i -e "s@^Icon=.*@Icon=$APPDIR/data/icons/256x256/dtool_logo_small.xpm@" "$APPDIR"/etc/dtool-lookup-gui.desktop
else
	echo "$APPDIR"/etc/dtool-lookup-gui.desktop is not writable
	exit 1
fi
