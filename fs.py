#!/usr/bin/env python
# coding: utf-8

import errno
import os
import re
import sys

import time
import k3confloader


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
