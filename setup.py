# DO NOT EDIT!!! built with `python _building/build_setup.py`
import setuptools
setuptools.setup(
    name="k3fs",
    packages=["k3fs"],
    version="0.1.6",
    license='MIT',
    description='File-system Utilities',
    long_description='# k3fs\n\n[![Build Status](https://travis-ci.com/pykit3/k3fs.svg?branch=master)](https://travis-ci.com/pykit3/k3fs)\n[![Documentation Status](https://readthedocs.org/projects/k3fs/badge/?version=stable)](https://k3fs.readthedocs.io/en/stable/?badge=stable)\n[![Package](https://img.shields.io/pypi/pyversions/k3fs)](https://pypi.org/project/k3fs)\n\nFile-system Utilities\n\nk3fs is a component of [pykit3] project: a python3 toolkit set.\n\n\n# Install\n\n```\npip install k3fs\n```\n\n# Synopsis\n\n```python\n>>> fwrite(\'/tmp/foo\', "content")\n\n>>> fread(\'/tmp/foo\')\n\'content\'\n>>> \'foo\' in ls_files(\'/tmp/\')\nTrue\n```\n\n#   Author\n\nZhang Yanpo (张炎泼) <drdr.xp@gmail.com>\n\n#   Copyright and License\n\nThe MIT License (MIT)\n\nCopyright (c) 2015 Zhang Yanpo (张炎泼) <drdr.xp@gmail.com>\n\n\n[pykit3]: https://github.com/pykit3',
    long_description_content_type="text/markdown",
    author='Zhang Yanpo',
    author_email='drdr.xp@gmail.com',
    url='https://github.com/pykit3/k3fs',
    keywords=['fs', 'file', 'dir'],
    python_requires='>=3.0',

    install_requires=['semantic_version~=2.8.5', 'jinja2~=2.11.2', 'PyYAML~=5.3.1', 'sphinx~=3.3.1', 'k3ut<0.2,>=0.1.15', 'k3confloader<0.2,>=0.1.1', 'k3thread<0.2,>=0.1.0', 'k3num<0.2,>=0.1.1', 'psutil>=5.8.0'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
    ] + ['Programming Language :: Python :: 3.6', 'Programming Language :: Python :: 3.7', 'Programming Language :: Python :: 3.8', 'Programming Language :: Python :: Implementation :: PyPy'],
)
