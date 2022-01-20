# from https://tipsfordev.com/build-python-script-to-single-exe-with-pyinstaller
import sys
from jinja2.loaders import FileSystemLoader


class PyInstallerPackageLoader(FileSystemLoader):
    """Load templates from packages deployed as part of a Pyinstaller build.  It is constructed with
    the name of the python package and the path to the templates in that
    package::
        loader = PackageLoader('mypackage', 'views')
    If the package path is not given, ``'templates'`` is assumed.
    Per default the template encoding is ``'utf-8'`` which can be changed
    by setting the `encoding` parameter to something else.  Due to the nature
    of eggs it's only possible to reload templates if the package was loaded
    from the file system and not a zip file.
    """

    def __init__(self, package_name, package_path="templates", encoding="utf-8"):
        # Use the standard pyinstaller convention of storing additional package files
        full_package_path = f"{sys._MEIPASS}/{package_name}/{package_path}"
        # Defer everything else to the FileSystemLoader
        super().__init__(full_package_path, encoding)


def patch_jinja2_package_loader():
    """Patching the jinja2 loader which fails to locate the template when called from a pyinstaller build."""

    if getattr(sys, "frozen", False):
        import jinja2
        jinja2.PackageLoader = PyInstallerPackageLoader

patch_jinja2_package_loader()
