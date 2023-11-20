import os
from subprocess import Popen

from setuptools import build_meta as _orig
from setuptools.build_meta import *

SOURCE_PATH = os.path.join(os.path.dirname(__file__), os.path.pardir, "dtool_lookup_gui")
TARGET_PATH = os.path.join(os.path.dirname(__file__), os.path.pardir, "dtool_lookup_gui")


def glib_compile_schemas(source_path, target_path):
    if not os.path.exists(target_path):
        os.makedirs(target_path)

    print(f"running glib-compile-schemas {source_path} --targetdir {target_path}")
    Popen(["glib-compile-schemas", source_path, "--targetdir", target_path],
          ).wait()


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    glib_compile_schemas(SOURCE_PATH, TARGET_PATH)
    return _orig.build_wheel(wheel_directory,
                             config_settings=config_settings,
                             metadata_directory=metadata_directory)


def build_sdist(sdist_directory, config_settings=None):
    glib_compile_schemas(SOURCE_PATH, TARGET_PATH)
    return _orig.build_wheel(sdist_directory, config_settings=config_settings)