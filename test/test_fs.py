#!/usr/bin/env python
# coding: utf-8

import os
import time
import unittest

import k3fs
import k3proc
import k3thread
import k3ut

dd = k3ut.dd

# k3fs/test/
this_base = os.path.dirname(__file__)

pyt = 'python'


class TestFS(unittest.TestCase):

    def test_makedirs(self):

        fn = '/tmp/pykit-ut-k3fs-foo'
        fn_part = ('/tmp', 'pykit-ut-k3fs-foo')
        dd('fn_part:', fn_part)

        force_remove(fn)

        dd('file is not a dir')
        with open(fn, 'w') as f:
            f.write('a')
        self.assertRaises(OSError, k3fs.makedirs, fn)
        os.unlink(fn)

        dd('no error if dir exist')
        os.mkdir(fn)
        k3fs.makedirs(fn)
        os.rmdir(fn)

        dd('single part path should be created')
        k3fs.makedirs(fn)
        self.assertTrue(os.path.isdir(fn))
        os.rmdir(fn)

        dd('multi part path should be created')
        k3fs.makedirs(*fn_part)
        self.assertTrue(os.path.isdir(fn), 'multi part path should be created')
        os.rmdir(fn)

        dd('default mode')
        k3fs.makedirs(fn)
        self.assertEqual(0o755, get_mode(fn))
        os.rmdir(fn)

        dd('specify mode')
        k3fs.makedirs(fn, mode=0o700)
        self.assertEqual(0o700, get_mode(fn))
        os.rmdir(fn)

        dd('specify uid/gid, to change uid, you need root privilege')
        # dd('changing uid/gid works if it raises error')
        # self.assertRaises(PermissionError, k3fs.makedirs, fn, uid=1, gid=1)
        k3fs.makedirs(fn, uid=1, gid=1)

    def test_ls_dirs(self):
        k3fs.makedirs('test_dir/sub_dir1/foo')
        k3fs.makedirs('test_dir/sub_dir2')
        k3fs.fwrite('test_dir/test_file', 'foo')

        sub_dirs = k3fs.ls_dirs('test_dir')
        self.assertListEqual(['sub_dir1', 'sub_dir2'], sub_dirs)

        # test multi path segment
        sub_dirs = k3fs.ls_dirs('test_dir', 'sub_dir1')
        self.assertListEqual(['foo'], sub_dirs)

        k3fs.remove('test_dir')

    def test_ls_files(self):

        k3fs.makedirs('test_dir/foo_dir')

        k3fs.fwrite('test_dir/foo1', 'foo1')
        k3fs.fwrite('test_dir/foo2', 'foo2')
        k3fs.fwrite('test_dir/foo21', 'foo21')
        k3fs.fwrite('test_dir/foo_dir/foo', 'foo')
        k3fs.fwrite('test_dir/foo_dir/bar', 'bar')

        self.assertEqual(['foo1', 'foo2', 'foo21'], k3fs.ls_files('test_dir'))
        self.assertEqual(['foo2'], k3fs.ls_files('test_dir', pattern='2$'))

        self.assertEqual(['bar', 'foo'], k3fs.ls_files('test_dir/foo_dir'))
        self.assertEqual(['bar'], k3fs.ls_files('test_dir/foo_dir', pattern='^b'))

        # test multi path segments
        self.assertEqual(['bar', 'foo'], k3fs.ls_files('test_dir', 'foo_dir'))

        k3fs.remove('test_dir')

    def test_makedirs_with_config(self):

        fn = '/tmp/pykit-ut-k3fs-foo'
        force_remove(fn)

        rc, out, err = k3proc.shell_script(pyt + ' ' + this_base + '/makedirs_with_config.py ' + fn,
                                           env=dict(PYTHONPATH=this_base + ':' + os.environ.get('PYTHONPATH'),
                                                    PATH=os.environ.get('PATH'))
                                           )

        dd('run makedirs_with_config.py: ', rc, out, err)

        self.assertEqual(0, rc, 'normal exit')
        self.assertEqual('2,3', out, 'uid,gid is defined in test/pykitconfig.py')

    def test_read_write_file(self):

        fn = '/tmp/pykit-ut-rw-file'
        force_remove(fn)

        dd('write/read file')
        k3fs.fwrite(fn, 'bar')
        self.assertEqual('bar', k3fs.fread(fn))

        # write with multi path segment
        k3fs.fwrite('/tmp', 'pykit-ut-rw-file', '123')
        self.assertEqual('123', k3fs.fread(fn))

        # read with multi path segment
        self.assertEqual('123', k3fs.fread('/tmp', 'pykit-ut-rw-file'))

        self.assertEqual(b'123', k3fs.fread(fn, mode='b'))

        dd('write/read 3MB file')
        cont = '123' * (1024**2)

        k3fs.fwrite(fn, cont)
        self.assertEqual(cont, k3fs.fread(fn))

        dd('write file with uid/gid')
        k3fs.fwrite(fn, '1', uid=1, gid=1)
        stat = os.stat(fn)
        self.assertEqual(1, stat.st_uid)
        self.assertEqual(1, stat.st_gid)

        force_remove(fn)

    def test_write_file_with_config(self):

        fn = '/tmp/pykit-ut-k3fs-foo'
        force_remove(fn)

        rc, out, err = k3proc.shell_script(pyt + ' ' + this_base + '/write_with_config.py ' + fn,
                                           env=dict(PYTHONPATH=this_base + ':' + os.environ.get('PYTHONPATH'))
                                           )

        dd('run write_with_config.py: ', rc, out, err)

        self.assertEqual(0, rc, 'normal exit')
        self.assertEqual('2,3', out, 'uid,gid is defined in test/pykitconfig.py')

        force_remove(fn)

    def test_write_file_atomically(self):

        fn = '/tmp/pykit-ut-k3fs-write-atomic'

        dd('atomically write file')

        cont_thread1 = 'cont_thread1'
        cont_thread2 = 'cont_thread2'

        os_fsync = os.fsync

        def _wait_fsync(fildes):
            time.sleep(3)

            os_fsync(fildes)

        os.fsync = _wait_fsync

        assert_ok = {'ok': True}

        def _write_wait(cont_write, cont_read, start_after, atomic):

            time.sleep(start_after)

            k3fs.fwrite(fn, cont_write, atomic=atomic)

            if cont_read != k3fs.fread(fn):
                assert_ok['ok'] = False

        force_remove(fn)
        # atomic=False
        #  time     file    thread1     thread2
        #   0      cont_1   w_cont_1    sleep()
        #  1.5     cont_2   sleep()     w_cont_2
        #   3      cont_2   return      sleep()
        #  4.5     cont_2    None       return

        ths = []
        th = k3thread.daemon(_write_wait,
                             args=(cont_thread1, cont_thread2, 0, False))
        ths.append(th)

        th = k3thread.daemon(_write_wait,
                             args=(cont_thread2, cont_thread2, 1.5, False))
        ths.append(th)

        for th in ths:
            th.join()
        self.assertTrue(assert_ok['ok'])

        force_remove(fn)
        # atomic=True
        #  time     file    thread1     thread2
        #   0       None    w_cont_1    sleep()
        #  1.5      None    sleep()     w_cont_2
        #   3      cont_1   return      sleep()
        #  4.5     cont_2    None       return

        ths = []
        th = k3thread.daemon(_write_wait,
                             args=(cont_thread1, cont_thread1, 0, True))
        ths.append(th)

        th = k3thread.daemon(_write_wait,
                             args=(cont_thread2, cont_thread2, 1.5, True))
        ths.append(th)

        for th in ths:
            th.join()
        self.assertTrue(assert_ok['ok'])

        os.fsync = os_fsync
        force_remove(fn)

    def test_remove_normal_file(self):

        f = 'pykit-ut-k3fs-remove-file-normal'
        fn = '/tmp/' + f
        force_remove(fn)

        k3fs.fwrite(fn, '', atomic=True)
        self.assertTrue(os.path.isfile(fn))

        k3fs.remove(fn)
        self.assertFalse(os.path.exists(fn))

        k3fs.fwrite('/tmp', f, '', atomic=True)
        self.assertTrue(os.path.isfile(fn))

        # remove with multi path segments
        k3fs.remove('/tmp', f)
        self.assertFalse(os.path.exists(fn))

    def test_remove_link_file(self):

        src_fn = '/tmp/pykit-ut-k3fs-remove-file-normal'
        force_remove(src_fn)

        k3fs.fwrite(src_fn, '', atomic=True)
        self.assertTrue(os.path.isfile(src_fn))

        link_fn = '/tmp/pykit-ut-k3fs-remove-file-link'
        force_remove(link_fn)

        os.link(src_fn, link_fn)
        self.assertTrue(os.path.isfile(link_fn))

        k3fs.remove(link_fn)
        self.assertFalse(os.path.exists(link_fn))

        symlink_fn = '/tmp/pykit-ut-k3fs-remove-file-symlink'
        force_remove(symlink_fn)

        os.symlink(src_fn, symlink_fn)
        self.assertTrue(os.path.islink(symlink_fn))

        k3fs.remove(symlink_fn)
        self.assertFalse(os.path.exists(symlink_fn))

        force_remove(src_fn)

    def test_remove_dir(self):

        dirname = '/tmp/pykit-ut-k3fs-remove-dir'

        k3fs.makedirs(dirname)
        self.assertTrue(os.path.isdir(dirname))

        for is_dir, file_path in (
                (False, ('normal_file',)),
                (True, ('sub_dir',)),
                (False, ('sub_dir', 'sub_file1')),
                (False, ('sub_dir', 'sub_file2')),
                (True, ('sub_empty_dir',)),
                (True, ('sub_dir', 'sub_sub_dir')),
                (False, ('sub_dir', 'sub_sub_dir', 'sub_sub_file')),
        ):

            path = os.path.join(dirname, *file_path)

            if is_dir:
                k3fs.makedirs(path)
                self.assertTrue(os.path.isdir(path))
            else:
                k3fs.fwrite(path, '')
                self.assertTrue(os.path.isfile(path))

        k3fs.remove(dirname)
        self.assertFalse(os.path.exists(dirname))

    def test_remove_dir_with_link(self):

        dirname = '/tmp/pykit-ut-k3fs-remove-dir'

        k3fs.makedirs(dirname)
        self.assertTrue(os.path.isdir(dirname))

        normal_file = 'normal_file'
        normal_path = os.path.join(dirname, normal_file)

        k3fs.fwrite(normal_path, '')
        self.assertTrue(os.path.isfile(normal_path))

        hard_link = 'hard_link'
        hard_path = os.path.join(dirname, hard_link)

        os.link(normal_path, hard_path)
        self.assertTrue(os.path.isfile(hard_path))

        symbolic_link = 'symbolic_link'
        symbolic_path = os.path.join(dirname, symbolic_link)

        os.symlink(hard_path, symbolic_path)
        self.assertTrue(os.path.islink(symbolic_path))

        k3fs.remove(dirname)
        self.assertFalse(os.path.exists(dirname))

    def test_remove_error(self):

        dirname = '/tmp/pykit-ut-k3fs-remove-on-error'
        if os.path.isdir(dirname):
            k3fs.remove(dirname)

        # OSError
        self.assertRaises(os.error, k3fs.remove, dirname, onerror='raise')

        # ignore errors
        k3fs.remove(dirname, onerror='ignore')

        def assert_error(exp_func):
            def onerror(func, path, exc_info):
                self.assertEqual(func, exp_func)
            return onerror

        # on error
        k3fs.remove(dirname, onerror=assert_error(os.remove))


def force_remove(fn):

    try:
        os.rmdir(fn)
    except BaseException:
        pass

    try:
        os.unlink(fn)
    except BaseException:
        pass


def get_mode(fn):
    mode = os.stat(fn).st_mode
    dd('mode read:', oct(mode))
    return mode & 0o777
