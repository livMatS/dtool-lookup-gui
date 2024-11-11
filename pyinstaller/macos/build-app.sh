brew install \
          python \
          glib \
          gobject-introspection \
          pygobject3 \
          gtk+3 \
          gtksourceview4 \
          adwaita-icon-theme \
          create-dmg \
          gfortran \
          numpy \
          scipy

python3.13 -m venv --system-site-packages venv
source venv/bin/activate

pip install --upgrade pip
pip install wheel setuptools_scm
pip install -r pyinstaller/macos/requirements.txt
pip install pyinstaller pyinstaller-hooks-contrib

cd dtool_lookup_gui && glib-compile-schemas . && cd ..

pyinstaller -y ./pyinstaller/macos/dtool-lookup-gui-macos.spec 2>&1 | tee pyinstaller.log

mv dist/dtool-lookup-gui.app dtool-lookup-gui.app
