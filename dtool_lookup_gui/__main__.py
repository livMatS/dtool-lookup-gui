#
# PYTHON_ARGCOMPLETE_OK
# Copyright 2020 Lars Pastewka
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

if __name__ == '__main__':
    import logging
    import argparse

    from . import GlobalConfig
    from .MainApplication import run_gui


    # in order to have both:
    # * preformatted help text and ...
    # * automatic display of defaults
    class ArgumentDefaultsAndRawDescriptionHelpFormatter(
        argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
        pass

    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=ArgumentDefaultsAndRawDescriptionHelpFormatter)

    parser.add_argument('--verbose', '-v', action='count', dest='verbose',
                        default=0, help='Make terminal output more verbose')
    parser.add_argument('--all-auto-refresh-off', action='store_true',
                        dest='all_auto_refresh_off', default=False,
                        help='Do not load any dataset lists at launch.')
    parser.add_argument('--debug', action='store_true',
                        help='Print debug info')

    try:
        import argcomplete
        argcomplete.autocomplete(parser)
    except ModuleNotFoundError as err:
        pass

    args = parser.parse_args()

    loglevel = logging.ERROR

    if args.verbose > 0:
        loglevel = logging.WARN
    if args.verbose > 1:
        loglevel = logging.INFO
    if args.debug or (args.verbose > 2):
        loglevel = logging.DEBUG

    # explicitly modify the root logger
    logging.basicConfig(level=loglevel)
    logger = logging.getLogger()
    logger.setLevel(loglevel)

    if args.all_auto_refresh_off:
        logger.debug("All auto refresh turned off via CLI flag.")
        GlobalConfig.auto_refresh_on = False

    run_gui()