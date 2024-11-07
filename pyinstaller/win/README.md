# Pyinstaller files

## Windows bundle

* `mingw64_pacman_S.txt` contains unpinned `mingw64` packages to install for building and bundling the app with `mingw64`.
  Packages may be installed with `pacman -S $(cat mingw64_pacman_S.txt | xargs)`.
* `mingw64_pacman_Q.txt` contains the latest `mingw64` package list the app has been successfully bundled with 
  output with `pacman -Q`.
* `requirements.in` contains the unpinned Python packages to install system-wide with `mingw64`.
* `requirements.txt` contains the latest Python packages the app has been built with.
  Can be generated with `pip-compile --upgrade mingw64_requirements.in > mingw64_requirements.txt`.
* `mingw64_venv_pip_freeze.txt` contains the output of `pip freeze` right before building the app.
* `mingw64_venv_pip_freeze_local.txt` contains the output of `pip freeze --local` right before building the app.

The typical workflow for building and bundling the app with `mingw64` while updating the version reference files looks like this:

```bash
pacman -S $(cat pyinstaller/win/mingw64_pacman_S.txt | xargs)
python -m pip install --upgrade pip

pip-compile --upgrade pyinstaller/win/requirements.in --output-file pyinstaller/win/full_requirements.txt

python maintenance/extract_toplevel_requirements.py

pip install -r pyinstaller/win/requirements.txt
 
pip install PyInstaller

python -m venv --system-site-packages venv
source venv/bin/activate
python -m pip install --upgrade pip

pip install --ignore-installed six

pip install pipdeptree

pip freeze --local | tee 
pyinstaller/win/mingw64_venv_pip_freeze_local.txt
pip freeze | tee pyinstaller/win/mingw64_venv_pip_freeze.txt

pipdeptree | tee pyinstaller/win/mingw64_venv_pipdeptree.txt
cd dtool_lookup_gui &&  glib-compile-schemas . && cd ..

python -m PyInstaller -y ./pyinstaller/win/dtool-lookup-gui-windows-one-file.spec
```
