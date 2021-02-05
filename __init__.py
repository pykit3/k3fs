"""
k3fs is collection of file-system operation utilities.

Usage::

    >>> fwrite('/tmp/foo', "content")

    >>> fread('/tmp/foo')
    'content'

    >>> 'foo' in ls_files('/tmp/')
    True

"""

__version__ = "0.1.4"
__name__ = "k3fs"

from .fs import fread
from .fs import fwrite
from .fs import ls_dirs
from .fs import ls_files
from .fs import makedirs
from .fs import remove

__all__ = [
    "ls_dirs",
    "ls_files",
    "makedirs",
    "fread",
    "fwrite",
    "remove",
]
