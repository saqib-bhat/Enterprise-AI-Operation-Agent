def test_python_version():
    import sys

    assert sys.version_info >= (3, 12), "Python 3.12 or newer is required"
