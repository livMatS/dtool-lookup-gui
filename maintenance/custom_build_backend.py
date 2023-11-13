import os
from subprocess import Popen

from setuptools import build_meta as _orig
from setuptools.build_meta import *


def glib_compile_schemas(root_path):
    Popen(["glib-compile-schemas", os.path.join(root_path, "dtool_lookup_gui")],
          ).wait()


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    glib_compile_schemas(wheel_directory)
    return _orig.build_wheel(wheel_directory,
                             config_settings=config_settings,
                             metadata_directory=metadata_directory)


def build_sdist(sdist_directory, config_settings=None):
    glib_compile_schemas(sdist_directory)
    return _orig.build_wheel(sdist_directory, config_settings=config_settings)