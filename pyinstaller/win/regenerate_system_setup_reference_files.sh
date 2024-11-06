#!/bin/bash
pacman -Q > pyinstaller/mingw64_pacman_Q.txt
pip freeze > pyinstaller/mingw64_venv_pip_freeze.txt
pip freeze --local > pyinstaller/mingw64_venv_pip_freeze_local.txt
