from pkg_resources import iter_entry_points

import dtoolcore
import dtool_lookup_api

try:
    from dtool import __version__ as dtool_version
except ImportError:
    dtool_version = None

from .. import __version__

# from https://github.com/jic-dtool/dtool-cli/blob/master/dtool_cli/cli.py
def pretty_version_text():
    """Return pretty version text listing all plugins."""
    if dtool_version is not None:
        version_lines = ["dtool, version {}".format(dtool_version)]
    else:
        version_lines = []
    version_lines.append("\n<b>Base</b>:")
    version_lines.append("dtoolcore, version {}".format(dtoolcore.__version__))
    version_lines.append("dtool-lookup-api, version {}".format(dtool_lookup_api.__version__))
    version_lines.append("dtool-lookup-gui, version {}".format(__version__))

    # List the storage broker packages.
    version_lines.append("\n<b>Storage brokers</b>:")
    for ep in iter_entry_points("dtool.storage_brokers"):
        package = ep.module_name.split(".")[0]
        dyn_load_p = __import__(package)
        version = dyn_load_p.__version__
        storage_broker = ep.load()
        version_lines.append(
            "{}, {}, version {}".format(
                storage_broker.key,
                package.replace("_", "-"),
                version))

    # List the plugin packages.
    modules = [ep.module_name for ep in iter_entry_points("dtool.cli")]
    packages = set([m.split(".")[0] for m in modules])
    version_lines.append("\n<b>Plugins</b>:")
    for p in packages:
        dyn_load_p = __import__(p)
        version_lines.append(
            "{}, version {}".format(
                p.replace("_", "-"),
                dyn_load_p.__version__))

    return "\n".join(version_lines)
