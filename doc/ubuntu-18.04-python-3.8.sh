# $ lsb_release -a
# LSB Version:    core-9.20170808ubuntu1-noarch:printing-9.20170808ubuntu1-noarch:security-9.20170808ubuntu1-noarch
# Distributor ID: Ubuntu
# Description:    Ubuntu 18.04.5 LTS
# Release:    18.04
# Codename:   bionic

# Python 3.8:
# https://linuxize.com/post/how-to-install-python-3-8-on-ubuntu-18-04/
sudo apt install software-properties-common
sudo apt install python3.8 python3.8-venv python3.8-dev
python3.8 -m venv ~/venv/dtool-python-3.8
source ~/venv/dtool-python-3.8/bin/activate
pip install --upgrade pip

# graph-tool requirements
pip install scipy
pip install matplotlib
pip install pycairo
pip install cairomm

sudo apt-get install libcairomm-1.0-dev
sudo apt-get install libcgal-dev
sudo apt-get install libsparsehash-dev

# graph-tool
git clone https://git.skewed.de/count0/graph-tool.git
cd graph-tool
./configure --prefix=$HOME/venv/dtool-python-3.8
# ================================================================================
#                              CONFIGURATION SUMMARY                              
# ================================================================================
# Using python version:   3.8.5
# Python interpreter:     /home/jotelha/venv/dtool-python-3.8/bin/python
# Installation path:      /home/jotelha/venv/dtool-python-3.8/lib/python3.8/site-packages/graph_tool
# 
# C++ compiler (CXX):     g++ -std=gnu++17
# C++ compiler version:   7
# 
# Prefix:                 /home/jotelha/venv/dtool-python-3.8
# Pkgconfigdir:           ${libdir}/pkgconfig
# 
# Python CPP flags:       -I/home/jotelha/venv/dtool-python-3.8/lib/python3.8/site-packages/cairo/include -I/usr/include/python3.8
# Python LD flags:        -L/usr/lib -lpython3.8
# Boost CPP flags:        -pthread -I/usr/include
# Boost LD flags:         -L/usr/lib/x86_64-linux-gnu -lboost_iostreams -lboost_python-py36 -lboost_regex -lboost_context -lboost_coroutine
# Numpy CPP flags:        -I/home/jotelha/venv/dtool-python-3.8/lib/python3.8/site-packages/numpy/core/include
# Sparsehash CPP flags:   
# CGAL CPP flags:         -I/usr/include
# CGAL LD flags:          
# Expat CPP flags:        -I/usr/include
# Expat LD flags:         -L/usr/lib -lexpat
# Cairomm CPP flags:      -I/usr/include/cairomm-1.0 -I/usr/lib/x86_64-linux-gnu/cairomm-1.0/include -I/usr/include/cairo -I/usr/include/glib-2.0 -I/usr/lib/x86_64-linux-gnu/glib-2.0/include -I/usr/include/pixman-1 -I/usr/include/freetype2 -I/usr/include/libpng16 -I/usr/include/freetype2 -I/usr/include/libpng16 -I/usr/include/sigc++-2.0 -I/usr/lib/x86_64-linux-gnu/sigc++-2.0/include
# Cairomm LD flags:       -lcairomm-1.0 -lcairo -lsigc-2.0
# OpenMP compiler flags:  -fopenmp
# OpenMP LD flags:        
# Extra CPPFLAGS:         -DNDEBUG 
# Extra CXXFLAGS:         -fopenmp -O3 -fvisibility=default -fvisibility-inlines-hidden -Wno-deprecated -Wall -Wextra -ftemplate-backtrace-limit=0  -Wno-register
# Extra LDFLAGS:          
# 
# Using OpenMP:           yes
# Using sparsehash:       yes
# Using cairo:            yes
# ================================================================================
make
make install

# dtool-lookup-gui
pip install git+https://github.com/IMTEK-Simulation/dtool-gui.git