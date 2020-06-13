import os
import sys

import k3fs

fn = sys.argv[1]

k3fs.fwrite(fn, 'boo')
stat = os.stat(fn)
os.write(1, '{uid},{gid}'.format(uid=stat.st_uid, gid=stat.st_gid).encode('utf-8'))
