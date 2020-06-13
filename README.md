# k3fs

[![Build Status](https://travis-ci.com/pykit3/k3fs.svg?branch=master)](https://travis-ci.com/pykit3/k3fs)
[![Documentation Status](https://readthedocs.org/projects/k3fs/badge/?version=stable)](https://k3fs.readthedocs.io/en/stable/?badge=stable)
[![Package](https://img.shields.io/pypi/pyversions/k3fs)](https://pypi.org/project/k3fs)

File-system Utilities

k3fs is a component of [pykit3] project: a python3 toolkit set.


# Install

```
pip install k3fs
```

# Synopsis

```python
>>> fwrite('/tmp/foo', "content")

>>> fread('/tmp/foo')
'content'
>>> 'foo' in ls_files('/tmp/')
True
```

#   Author

Zhang Yanpo (张炎泼) <drdr.xp@gmail.com>

#   Copyright and License

The MIT License (MIT)

Copyright (c) 2015 Zhang Yanpo (张炎泼) <drdr.xp@gmail.com>


[pykit3]: https://github.com/pykit3