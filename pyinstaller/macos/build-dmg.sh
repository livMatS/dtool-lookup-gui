#!/bin/bash

mkdir -p release

bash maintenance/copy_files_into_folders.sh \
    pyinstaller/MANIFEST.macos-release release

create-dmg \
            --volname "dtool-lookup-gui" \
            --eula "LICENSE.txt" \
            --volicon "data/icons/dtool_logo.icns" \
            --window-pos 200 120 \
            --window-size 600 300 \
            --icon-size 100 \
            --icon "dtool-lookup-gui.app" 175 120 \
            --hide-extension "dtool-lookup-gui.app" \
            --app-drop-link 425 120 \
            --hdiutil-verbose \
            "dtool-lookup-gui-macos.dmg" \
            "release/"
