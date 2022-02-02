import logging
import os
import socket

from dtoolcore.utils import IS_WINDOWS, windows_to_unix_path

import dtoolcore.utils

try:
    from urlparse import urlparse, urlunparse
except ImportError:
    from urllib.parse import urlparse, urlunparse

logger = logging.getLogger(__name__)

def generous_parse_uri(uri):
    """Return a urlparse.ParseResult object with the results of parsing the
    given URI. This has the same properties as the result of parse_uri.
    When passed a relative path, it determines the absolute path, sets the
    scheme to file, the netloc to localhost and returns a parse of the result.
    """
    logger.debug("In generous_pase_uri...")
    logger.debug("generous_pase_uri.input_uri: {}".format(uri))

    parse_result = urlparse(uri)

    IS_WINDOWS_DRIVE_LETTER = len(parse_result.scheme) == 1

    if parse_result.scheme == '' or IS_WINDOWS_DRIVE_LETTER:
        # ATTENTION: abspath apparently prepends the drive letter of the current working directory on Windows
        if IS_WINDOWS_DRIVE_LETTER:
            abspath = parse_result.scheme.upper() + ':' + parse_result.path
        else:
            abspath = os.path.abspath(parse_result.path)

        fixed_uri = "file://{}{}".format(
            socket.gethostname(),
            abspath
        )
        if IS_WINDOWS:
            abspath = windows_to_unix_path(abspath)
            fixed_uri = "file:///{}".format(abspath)
        parse_result = urlparse(fixed_uri)

    logger.debug("generouse_pase_uri.return: {}".format(parse_result))
    return parse_result

# as of dtoolcore v3.18.1, we have to patch dtoolcore.utils.generous_parse_uri
# to avoid a drive letter issue on windows. Otherwise, any drive letter within
# a local windows path will be replaced by the drive letter of the current
# working directory. See for example
#   $ cygpath -wa .
#   C:\msys64\home\
#   $ python -c 'import os; from urllib.parse import urlparse; parse_result = urlparse("D:/test/path"); print(os.path.abspath(parse_result.path))'
#   C:/test/path
dtoolcore.utils.generous_parse_uri = generous_parse_uri