#!/bin/bash
pyinstaller --windowed --debug=all \
    --runtime-hook ./pyinstaller/rthooks/pyi_rth_jinja2.py \
    --paths $HOME/venv/20220120-dtool-lookup-gui/lib/python3.8/site-packages \
    --name dtool-lookup-gui dtool_lookup_gui/launcher.py
