# Pyinstaller files

## Content

* dtool-lookup-gui-(linux|windows|macos).spec - pyinstaller spec files for building application bundle in folder on different systems
* dtool-lookup-gui-(linux|windows|macos)-one-file.spec - pyinstaller spec files for building single-file portable application on different systems
* `MANIFEST.general` - files included in any release
* `MANIFEST.(linux|windows|macos)` - files included in workflow artifact, includes description of build system
* `MANIFEST.(linux|windows|macos)-release` - files included in systems-pecific release
* `hooks` - custom build-time hooks for pyinstaller
* `rthooks` - custom run-time hooks for pyinstaller 

## Windows bundle

* `mingw64_pacman_S.txt` contains unpinned `mingw64` packages to install for building and bundling the app with `mingw64`.
  Packages may be installed with `pacman -S $(cat mingw64_pacman_S.txt | xargs)`.
* `mingw64_pacman_Q.txt` contains the latest `mingw64` package list the app has been successfully bundled with 
  output with `pacman -Q`.
* `mingw64_requirements.in` contains the unpinned Python packages to install system-wide with `mingw64`.
* `mingw64_requirements.txt` contains the latest Python packages the app has been built with.
  Can be generated with `pip-compile --upgrade mingw64_requirements.in > mingw64_requirements.txt`.
* `mingw64_venv_pip_freeze.txt` contains the output of `pip freeze` right before building the app.
* `mingw64_venv_pip_freeze_local.txt` contains the output of `pip freeze --local` right before building the app.

The typical workflow for building and bundling the app with `mingw64` while updating the version reference files looks like this:

```bash
pacman -S $(cat pyinstaller/mingw64_pacman_S.txt | xargs)
python -m pip install --upgrade pip

pip-compile --upgrade pyinstaller/mingw64_requirements.in --output-file pyinstaller/mingw64_requirements.txt

pip install --ignore-installed -r pyinstaller/mingw64_requirements.txt
pip install PyInstaller

python -m venv --system-site-packages venv
source venv/bin/activate
pip install --ignore-installed six

pip freeze --local | tee pyinstaller/mingw64_venv_pip_freeze_local.txt
pip freeze | tee pyinstaller/mingw64_venv_pip_freeze.txt

cd dtool_lookup_gui &&  glib-compile-schemas . && cd ..

python -m PyInstaller -y ./pyinstaller/dtool-lookup-gui-windows-one-file.spec
```