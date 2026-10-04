import os
import sys

import k3fs

fn = sys.argv[1]

k3fs.makedirs(fn)
stat = os.stat(fn)
os.write(1, f"{stat.st_uid},{stat.st_gid}".encode())
