# Pyinstaller files

## Content

* dtool-lookup-gui-(linux|windows|macos).spec - pyinstaller spec files for building application bundle in folder on different systems
* dtool-lookup-gui-(linux|windows|macos)-one-file.spec - pyinstaller spec files for building single-file portable application on different systems
* `MANIFEST.general` - files included in any release
* `MANIFEST.(linux|windows|macos)` - files included in workflow artifact, includes description of build system
* `MANIFEST.(linux|windows|macos)-release` - files included in systems-pecific release
* `hooks` - custom build-time hooks for pyinstaller
* `rthooks` - custom run-time hooks for pyinstaller 
