# https://git.skewed.de/count0/graph-tool/-/wikis/installation-instructions#debian-ubuntu
echo "deb [ arch=amd64 ] https://downloads.skewed.de/apt bionic main" | sudo tee -a /etc/apt/sources.list
sudo apt-key adv --keyserver keys.openpgp.org --recv-key 612DEFB798507F25
sudo apt-get install python3-graph-tool

# venv
python3.6 -m venv --system-site-packages ~/venv/dtool-python-3.6
source ~/venv/dtool-python-3.6/bin/activate

# dtool_lookup_gui
pip install git+https://github.com/IMTEK-Simulation/dtool-gui.git