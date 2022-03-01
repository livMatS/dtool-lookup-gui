import logging
import os

from .logging import _log_nested


class TemporaryOSEnviron:
    """Preserve original os.environ context manager."""

    def __init__(self, env=None):
        """env is a flat dict to be inserted into os.environ."""
        self._insertions = env

    def __enter__(self):
        """Store backup of current os.environ."""
        logger = logging.getLogger(__name__)
        logger.debug("Backed-up os.environ:")
        _log_nested(logger.debug, dict(os.environ))
        self._original_environ = dict(os.environ.copy())

        if self._insertions:
            for k, v in self._insertions.items():
                logger.debug("Inject env var '{}' = '{}'".format(k, v))
                os.environ[k] = str(v)

        logger.debug("Initial modified os.environ:")
        _log_nested(logger.debug, dict(os.environ))

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore backed up os.environ."""
        logger = logging.getLogger(__name__)
        os.environ.clear()
        os.environ.update(self._original_environ)
        logger.debug("Recovered os.environ:")
        _log_nested(logger.debug, dict(os.environ))