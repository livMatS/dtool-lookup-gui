#
# Copyright 2020-2022 Johannes Laurin Hörmann
#           2020-2021 Lars Pastewka
#           2020 Antoine Sanner
#
# ### MIT license
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import os
from subprocess import Popen

from setuptools import setup
from setuptools.command.install import install


class CustomInstallCommand(install):
    def run(self):
        install.run(self)
        Popen("glib-compile-schemas " + self.install_lib + "/dtool_lookup_gui/",
              shell=True).wait()


def local_scheme(version):
    """Skip the local version (eg. +xyz of 0.6.1.dev4+gdf99fe2)
    to be able to upload to Test PyPI"""
    return ""


url = 'https://github.com/livMatS/dtool-lookup-gui'
readme = open('README.rst', encoding="utf8").read()

setup(
    cmdclass={
        'install': CustomInstallCommand,
    },
    name='dtool-lookup-gui',
    packages=['dtool_lookup_gui'],
    description='Graphical user interface for dtool',
    long_description=readme,
    include_package_data=True,
    author='Lars Pastewka',
    author_email='lars.pastewka@imtek.uni-freiburg.de',
    url=url,
    use_scm_version={
        "local_scheme": local_scheme,
        "root": '.',
        "relative_to": __file__,
        "write_to": os.path.join(
            "dtool_lookup_gui", "version.py"),
    },
    install_requires=[
        'dtoolcore>=3.17',
        'dtool-create>=0.23.4',
        'dtool-info>=0.16.2',
        'dtool-lookup-api>=0.5',
        'aiohttp>=3.6',
        'gbulb>=0.6',
        'pyyaml>=5.3',
        'ruamel.yaml',
        'PyGObject>=3.36',
        'scipy>=1.5',
        'numpy',
        'jwt'
    ],
    setup_requires=[
        'setuptools_scm>=3.5.0'
    ],
    license='MIT'
)
