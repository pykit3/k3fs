# k3fs

[![Action-CI](https://github.com/pykit3/k3fs/actions/workflows/python-package.yml/badge.svg)](https://github.com/pykit3/k3fs/actions/workflows/python-package.yml)
[![Documentation Status](https://readthedocs.org/projects/k3fs/badge/?version=stable)](https://k3fs.readthedocs.io/en/stable/?badge=stable)
[![Package](https://img.shields.io/pypi/pyversions/k3fs)](https://pypi.org/project/k3fs)

File-system utilities for reading, writing, and directory operations.

k3fs is a component of [pykit3](https://github.com/pykit3) project: a python3 toolkit set.

## Installation

```bash
pip install k3fs
```

## Quick Start

```python
>>> from k3fs import fwrite, fread, ls_files

>>> fwrite('/tmp/foo', "content")

>>> fread('/tmp/foo')
'content'

>>> 'foo' in ls_files('/tmp/')
True
```

## API Reference

::: k3fs

## License

The MIT License (MIT) - Copyright (c) 2015 Zhang Yanpo (张炎泼)
