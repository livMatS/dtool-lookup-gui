"""Skeleton defining the dtool plugin entry points."""

import os
import logging

try:
    from importlib.metadata import entry_points as _entry_points
    def iter_entry_points(group, name=None):
        eps = _entry_points(group=group)
        if name is not None:
            eps = [ep for ep in eps if ep.name == name]
        return eps
except ImportError:
    from pkg_resources import iter_entry_points

import click
from click_plugins import with_plugins

import dtoolcore
import dtoolcore.utils

try:
    from dtool import __version__ as dtool_version
except ImportError:
    dtool_version = ""

from . import __version__

_CLICK_CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
CONFIG_PATH = os.path.expanduser("~/.config/dtool/dtool.json")


def storagebroker_validation(ctx, param, value):
    storage_broker_lookup = dtoolcore._generate_storage_broker_lookup()
    if value not in storage_broker_lookup:
        raise click.BadParameter(
            "'{}' not in {}".format(value, storage_broker_lookup.keys()))
    return value


def base_dataset_uri_validation(ctx, param, value):
    value = dtoolcore.utils.sanitise_uri(value)
    if not dtoolcore._is_dataset(value, config_path=CONFIG_PATH):
        raise click.BadParameter(
            "URI is not a dataset: {}".format(value))
    return value


def proto_dataset_uri_validation(ctx, param, value):
    value = base_dataset_uri_validation(ctx, param, value)
    admin_metadata = dtoolcore._admin_metadata_from_uri(
        uri=value,
        config_path=CONFIG_PATH
    )
    if admin_metadata["type"] != "protodataset":
        message_lines = [
            "\nURI is not a proto dataset: {}".format(value),
            "It looks like a frozen dataset",
        ]
        raise click.BadParameter("\n".join(message_lines))
    return value


def dataset_uri_validation(ctx, param, value):
    value = base_dataset_uri_validation(ctx, param, value)
    admin_metadata = dtoolcore._admin_metadata_from_uri(
        uri=value,
        config_path=CONFIG_PATH
    )
    if admin_metadata["type"] != "dataset":
        message_lines = [
            "\nURI is not a frozen dataset: {}".format(value),
            "It looks like a proto dataset",
        ]
        raise click.BadParameter("\n".join(message_lines))
    return value


base_dataset_uri_argument = click.argument(
    "dataset_uri",
    callback=base_dataset_uri_validation
)


proto_dataset_uri_argument = click.argument(
    "proto_dataset_uri",
    callback=proto_dataset_uri_validation
)


dataset_uri_argument = click.argument(
    "dataset_uri",
    callback=dataset_uri_validation
)


def pretty_version_text():
    """Return pretty version text listing all plugins."""
    version_lines = ["dtool, version {}".format(dtool_version)]
    version_lines.append("\nBase:")
    version_lines.append("dtoolcore, version {}".format(dtoolcore.__version__))
    version_lines.append("dtool-cli, version {}".format(__version__))

    # List the storage broker packages.
    version_lines.append("\nStorage brokers:")
    for ep in iter_entry_points("dtool.storage_brokers"):
        package = ep.value.split(":")[0].split(".")[0]
        dyn_load_p = __import__(package)
        version = dyn_load_p.__version__
        storage_broker = ep.load()
        version_lines.append(
            "{}, {}, version {}".format(
                storage_broker.key,
                package.replace("_", "-"),
                version))

    # List the plugin packages.
    modules = [ep.value.split(":")[0] for ep in iter_entry_points("dtool.cli")]
    packages = set([m.split(".")[0] for m in modules])
    version_lines.append("\nPlugins:")
    for p in packages:
        dyn_load_p = __import__(p)
        version_lines.append(
            "{}, version {}".format(
                p.replace("_", "-"),
                dyn_load_p.__version__))

    return "\n".join(version_lines)


@with_plugins(iter_entry_points("dtool.cli"))
@click.group(context_settings=_CLICK_CONTEXT_SETTINGS)
@click.version_option(message=pretty_version_text() if not getattr(__import__('sys'), '_MEIPASS', None) else 'dtool')
@click.option("--debug", is_flag=True, help="Turn on debugging output.")
def dtool(debug):
    """Tool to work with datasets."""
    level = logging.WARNING
    if debug:
        level = logging.DEBUG
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=level)
