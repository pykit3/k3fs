import os
import sys

import k3fs

fn = sys.argv[1]
# The optional sys.argv[2:] are a uid and a gid to pass instead of the ones in test/k3conf.py.
ids = {}
if len(sys.argv) > 2:
    ids = {"uid": int(sys.argv[2]), "gid": int(sys.argv[3])}

k3fs.fwrite(fn, "boo", **ids)
stat = os.stat(fn)
os.write(1, f"{stat.st_uid},{stat.st_gid}".encode())
