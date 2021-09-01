#!/usr/bin/env python
# coding: utf-8

import binascii
import hashlib
import errno
import os
import re
import sys
import psutil

import time
import k3confloader

READ_BLOCK = 32 * 1024 * 1024
WRITE_BLOCK = 32 * 1024 * 1024


class FSUtilError(Exception):
    pass


class NotMountPoint(FSUtilError):
    pass


def assert_mountpoint(path):
    """
    Ensure that `path` must be a **mount point**.
    Or an error `NotMountPoint` is emitted.
    :param path: is a path that does have to be an existent file path.
    :return: Nothing
    """
    if not os.path.ismount(path):
        raise NotMountPoint(path)


def get_all_mountpoint(all=False):
    """
    Returns a list of all mount points on this host.
    :param all: specifies if to return non-physical device mount points.
    :return: By default it is `False` thus only disk drive mount points are returned.
    `tmpfs` or `/proc` are not returned by default.
    """
    partitions = psutil.disk_partitions(all=all)
    prt_by_mp = [x.mountpoint for x in partitions]
    return prt_by_mp


def get_mountpoint(path):
    """
    Return the mount point where this `path` resides on.
    All symbolic links are resolved when looking up for mount point.
    :param path: is a path that does have to be an existent file path.
    :return: the mount point path(one of output of command `mount` on linux)
    """
    path = os.path.realpath(path)

    prt_by_mountpoint = get_disk_partitions()

    while path != '/' and path not in prt_by_mountpoint:
        path = os.path.dirname(path)

    return path


def get_device(path):
    """
    Get the device path(`/dev/sdb` etc) where `path` resides on.
    :param path: is a path that does have to be an existent file path.
    :return: device path like `"/dev/sdb"` in string.
    """

    prt_by_mountpoint = get_disk_partitions()

    mp = get_mountpoint(path)

    return prt_by_mountpoint[mp]['device']


def get_device_fs(device):
    """
    Return the file-system name of a device, if the device is a disk device.
    :param device: is a path of a device, such as `/dev/sdb1`.
    :return: the file-system name, such as `ext4` or `hfs`.
    """
    prt_by_mp = get_disk_partitions()

    for prt in list(prt_by_mp.values()):
        if device == prt['device']:
            return prt['fstype']
    else:
        return 'unknown'


def get_disk_partitions(all=True):
    """
    Find and return all mounted path and its mount point information in a
    dictionary.
    :param all:  By default it is `True` thus all mount points including non-disk path are also returned,
    otherwise `tmpfs` or `/proc` are not returned.
    :return: an dictionary indexed by mount point path:
    """
    # {
    #     '/': {'device': '/dev/disk1',
    #           'fstype': 'hfs',
    #           'mountpoint': '/',
    #           'opts': 'rw,local,rootfs,dovolfs,journaled,multilabel'},
    #     '/dev': {'device': 'devfs',
    #              'fstype': 'devfs',
    #              'mountpoint': '/dev',
    #              'opts': 'rw,local,dontbrowse,multilabel'},
    #     '/home': {'device': 'map auto_home',
    #               'fstype': 'autofs',
    #               'mountpoint': '/home',
    #               'opts': 'rw,dontbrowse,automounted,multilabel'},
    #     '/net': {'device': 'map -hosts',
    #              'fstype': 'autofs',
    #              'mountpoint': '/net',
    #              'opts': 'rw,nosuid,dontbrowse,automounted,multilabel'}
    # }
    partitions = psutil.disk_partitions(all=all)

    by_mount_point = {}
    for pt in partitions:
        # OrderedDict([
        #      ('device', '/dev/disk1'),
        #      ('mountpoint', '/'),
        #      ('fstype', 'hfs'),
        #      ('opts', 'rw,local,rootfs,dovolfs,journaled,multilabel')])
        by_mount_point[pt.mountpoint] = _to_dict(pt)

    return by_mount_point


def get_path_fs(path):
    """
    Return the name of device where the `path` is mounted.
    :param path: is a file path on a file system.
    :return: the file-system name, such as `ext4` or `hfs`.
    """
    mp = get_mountpoint(path)
    prt_by_mp = get_disk_partitions()

    return prt_by_mp[mp]['fstype']


def get_path_usage(path):
    """
    Collect space usage information of the file system `path` is mounted on.
    :param path: specifies the fs-path to collect usage info. Such as `/tmp` or `/home/alice`.
    :return:
    a dictionary in the following format:
    {
        'total':     total space in byte,
        'used':      used space in byte(includes space reserved for super user),
        'available': total - used,
        'percent':   float(used) / 'total',
    }
    """
    space_st = os.statvfs(path)

    # f_bavail: without blocks reserved for super users
    # f_bfree:  with    blocks reserved for super users
    avail = space_st.f_frsize * space_st.f_bavail

    capa = space_st.f_frsize * space_st.f_blocks
    used = capa - avail

    return {
        'total': capa,
        'used': used,
        'available': avail,
        'percent': float(used) / capa,
    }


def get_path_inode_usage(path):
    """
    Collect inode usage information of the file system `path` is mounted on.
    :param path: specifies the fs - path to collect usage info.
    Such as `/tmp` or `/home/alice`.
    :return: a dictionary in the following format:
    """
    # ```json
    # {
    #     'total':     total number of inode,
    # 'used':      used inode(includes inode reserved for super user),
    # 'available': total - used,
    #              'percent':   float(used) / 'total'
    # }
    # ```
    inode_st = os.statvfs(path)

    available = inode_st.f_favail
    total = inode_st.f_files
    used = total - available

    return {
        'total': total,
        'used': used,
        'available': available,
        'percent': float(used) / total,
    }

def makedirs(*paths, **kwargs):
    """
    Make directory.
    If intermediate directory does not exist, create them too.

    Args:

        paths:
            is a single part path such as `/tmp/foo` or a separated path such as
            `('/tmp', 'foo')`.

        mode(int):
            specifies permission mode for the dir created or existed.
            By defaul it is `0755`.

        uid(int): specifies uid for the created dir.
            By default they are `None` and the created dir inherits ownership from the
            running python program.

        gid(int): specifies uid for the created dir.
            By default they are `None` and the created dir inherits ownership from the
            running python program.

    Raises:
        OSError: if trying to create dir with the same path of a non-dir file,
            or having other issue like permission denied.
    """

    mode = kwargs.get('mode', 0o755)
    uid = kwargs.get('uid') or k3confloader.conf.uid
    gid = kwargs.get('gid') or k3confloader.conf.gid

    path = os.path.join(*paths)
    last_err = None

    # retry to deal with concurrent check-and-then-set issue
    for _ in range(2):

        if os.path.isdir(path):

            if uid is not None and gid is not None:
                os.chown(path, uid, gid)

            return

        try:
            os.makedirs(path, mode=mode)
            if uid is not None and gid is not None:
                os.chown(path, uid, gid)
        except OSError as e:
            if e.errno == errno.EEXIST:
                last_err = e
                # concurrent if-exist and makedirs
            else:
                raise
    else:
        raise last_err


def ls_dirs(*paths):
    """
    Get sorted sub directories of `paths`.

    Args:
        paths:
            is the directory path.

    Returns:
        list: of all sub directory names.
    """

    path = os.path.join(*paths)
    files = os.listdir(path)

    sub_dirs = []
    for f in files:
        if os.path.isdir(os.path.join(path, f)):
            sub_dirs.append(f)

    sub_dirs.sort()

    return sub_dirs


def ls_files(*paths, pattern='.*'):
    """
    List all files that match `pattern` in `path`.

    Args:

        paths:
            is a directory path.

        pattern(str):
            is a regular expression that matches wanted file names.

    Returns:
        list: of sorted file names.
    """

    path = os.path.join(*paths)
    fns = os.listdir(path)

    pt = re.compile(pattern)

    fns = sorted([x for x in fns
                  if re.search(pt, x) is not None
                  and os.path.isfile(os.path.join(path, x))
                  ])

    return fns


def fread(*paths, mode=''):
    """
    Read and return the entire file specified by `path`

    Args:

        paths:
            is the path of the file to read.

        mode(str):
            If `mode='b'` it returns `bytes`.
            If `mode=''` it returns a `str` decoded from `bytes`.

    Returns:
        file content in string or bytes.
    """
    path = os.path.join(*paths)
    with open(path, 'r' + mode) as f:
        return f.read()


def fwrite(*paths_content, uid=None, gid=None, atomic=False, fsync=True):
    """
    Write `fcont` into file `path`.

    Args

        paths_content:
            is the file path to write to and the content to write.
            The last elt is content, e.g.:
            `fwrite('/tmp', 'foo', 'bar')` write 'bar' into file '/tmp/foo'.

        uid:
            specifies the user_id the file belongs to.

        gid:
            specifies the group_id the file belongs to.

            By default they are `None`, which means the file that has been written
            inheirts ownership of the running python script.

        atomic(bool):
            atomically write fcont to the path.

            Write fcont to a temporary file, then rename to the path.
            The temporary file names of same path in one process distinguish with
            nanosecond, it is not atomic if the temporary files of same path
            created at the same nanosecond.
            The renaming will be an atomic operation (this is a POSIX requirement).

        fsync(bool):
            specify if need to synchronize data to storage device.

    """

    fcont = paths_content[-1]
    path = os.path.join(*paths_content[:-1])
    if not atomic:
        return _write_file(path, fcont, uid, gid, fsync)

    tmp_path = '{path}._tmp_.{pid}_{timestamp}'.format(
        path=path,
        pid=os.getpid(),
        timestamp=int(time.time() * (1000 ** 3)),
    )
    _write_file(tmp_path, fcont, uid, gid, fsync)

    try:
        os.rename(tmp_path, path)
    except EnvironmentError:
        os.remove(tmp_path)
        raise


def _write_file(path, fcont, uid=None, gid=None, fsync=True):

    uid = uid or k3confloader.conf.uid
    gid = gid or k3confloader.conf.gid

    with open(path, 'w') as f:
        f.write(fcont)
        f.flush()
        if fsync:
            os.fsync(f.fileno())

    if uid is not None and gid is not None:
        os.chown(path, uid, gid)


def remove(*paths, onerror=None):
    """
    Recursively delete `path`, the `path` is *file*, *directory* or *symbolic link*.

    Args:

        paths:
            is the path to remove.

        onerror(str or callable):
            - "raise": when error occur it raises the original error.
            - "ignore": ignore error and go on.
            - A callable:
                it is called to handle the error with arguments `(func, path,
                exc_info)` where func is *os.listdir*, *os.remove*, *os.rmdir*
                or *os.path.isdir*.
    """

    path = os.path.join(*paths)

    if onerror is None:
        onerror = 'raise'

    try:
        is_dir = os.path.isdir(path)
    except os.error as e:
        if onerror == 'raise':
            raise e
        elif onerror == 'ignore':
            pass
        else:
            onerror(os.path.isdir, path, sys.exc_info())

        return

    if not is_dir:
        try:
            os.remove(path)
        except os.error as e:
            if onerror == 'raise':
                raise e
            elif onerror == 'ignore':
                pass
            else:
                onerror(os.remove, path, sys.exc_info())
        return

    names = []
    try:
        names = os.listdir(path)
    except os.error as e:
        if onerror == 'raise':
            raise e
        elif onerror == 'ignore':
            pass
        else:
            onerror(os.listdir, path, sys.exc_info())

    for name in names:
        fullname = os.path.join(path, name)
        remove(fullname, onerror=onerror)

    try:
        os.rmdir(path)
    except os.error as e:
        if onerror == 'raise':
            raise e
        elif onerror == 'ignore':
            pass
        else:
            onerror(os.rmdir, path, sys.exc_info())

def calc_checksums(path, sha1=False, md5=False, crc32=False, sha256=False,
                   block_size=READ_BLOCK, io_limit=READ_BLOCK):

    checksums = {
        'sha1': None,
        'md5': None,
        'crc32': None,
        'sha256': None
    }

    if (sha1 or md5 or crc32 or sha256) is False:
        return checksums

    if block_size <= 0:
        raise FSUtilError('block_size must be positive integer')

    if io_limit == 0:
        raise FSUtilError('io_limit shoud not be zero')

    min_io_time = float(block_size) / io_limit

    sum_sha1 = hashlib.sha1()
    sum_md5 = hashlib.md5()
    sum_crc32 = 0
    sum_sha256 = hashlib.sha256()

    with open(path, 'rb') as f_path:

        while True:
            t0 = time.time()

            buf = f_path.read(block_size)
            if len(buf) == 0:
                break

            t1 = time.time()

            time_sleep = max(0, min_io_time - (t1 - t0))
            if time_sleep > 0:
                time.sleep(time_sleep)

            if sha1:
                sum_sha1.update(buf)
            if md5:
                sum_md5.update(buf)
            if crc32:
                sum_crc32 = binascii.crc32(buf, sum_crc32)
            if sha256:
                sum_sha256.update(buf)

    if sha1:
        checksums['sha1'] = sum_sha1.hexdigest()
    if md5:
        checksums['md5'] = sum_md5.hexdigest()
    if crc32:
        checksums['crc32'] = '%08x' % (sum_crc32 & 0xffffffff)
    if sha256:
        checksums['sha256'] = sum_sha256.hexdigest()

    return checksums

def _to_dict(_namedtuple):
    return dict(_namedtuple._asdict())
