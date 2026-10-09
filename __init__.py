"""
k3fs is collection of file-system operation utilities.

Usage::

    >>> fwrite('/tmp/foo', "content")

    >>> fread('/tmp/foo')
    'content'

    >>> 'foo' in ls_files('/tmp/')
    True

"""

from .fs import (
    FSUtilError,
    NotMountPoint,
    assert_mountpoint,
    calc_checksums,
    fread,
    fwrite,
    get_all_mountpoint,
    get_device,
    get_device_fs,
    get_disk_partitions,
    get_mountpoint,
    get_path_fs,
    get_path_inode_usage,
    get_path_usage,
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
    "fread",
    "fwrite",
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
    "remove",
]


def __getattr__(name: str) -> str:
    # importlib.metadata takes about 20 ms to import, so it is loaded only
    # when __version__ is read
    if name != "__version__":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from importlib.metadata import version

    return version("k3fs")
