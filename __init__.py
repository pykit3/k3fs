"""
k3fs is collection of file-system operation utilities.

Usage::

    >>> fwrite('/tmp/foo', "content")

    >>> fread('/tmp/foo')
    'content'

    >>> 'foo' in ls_files('/tmp/')
    True

"""

__version__ = "0.1.6"
__name__ = "k3fs"
from .fs import (
    FSUtilError,
    NotMountPoint,

    assert_mountpoint,
    calc_checksums,
    get_all_mountpoint,
    get_device,
    get_device_fs,
    get_disk_partitions,
    get_mountpoint,
    get_path_fs,
    get_path_inode_usage,
    get_path_usage,

    fread,
    fwrite,
    ls_dirs,
    ls_files,
    makedirs,
    remove,
)
__all__ = [
    "FSUtilError",
    "NotMountPoint",
    "assert_mountpoint",
    "calc_checksums",
    "get_all_mountpoint",
    "get_device",
    "get_device_fs",
    "get_disk_partitions",
    "get_mountpoint",
    "get_path_fs",
    "get_path_inode_usage",
    "get_path_usage",

    "ls_dirs",
    "ls_files",
    "makedirs",
    "fread",
    "fwrite",
    "remove",
]
