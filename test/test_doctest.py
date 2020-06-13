import doctest

import pkgname


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(pkgname))
    return tests
