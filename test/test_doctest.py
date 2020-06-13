import doctest

import k3fs


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(k3fs))
    return tests
