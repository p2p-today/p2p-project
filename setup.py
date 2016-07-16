from __future__ import with_statement

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from py_src import __version__

classifiers = ['Development Status :: 3 - Alpha',
               'Intended Audience :: Developers',
               'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
               'Operating System :: OS Independent',
               'Topic :: Communications',
               'Topic :: Internet',
               'Programming Language :: JavaScript',
               'Programming Language :: Python']

classifiers.extend([
               ('Programming Language :: Python :: %s' % x) for x in
                '2 3 2.6 2.7 3.3 3.4 3.5'.split()])

loc = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(loc, 'py_src', 'README.rst'), 'r') as fd:
    long_description = fd.read()

def has_environment_marker_support():
    """
    Tests that setuptools has support for PEP-426 environment marker support.
    The first known release to support it is 0.7 (and the earliest on PyPI seems to be 0.7.2
    so we're using that), see: http://pythonhosted.org/setuptools/history.html#id142
    References:
    * https://wheel.readthedocs.io/en/latest/index.html#defining-conditional-dependencies
    * https://www.python.org/dev/peps/pep-0426/#environment-markers
    Method extended from pytest. Credit goes to developers there.
    """
    try:
        from pkg_resources import parse_version
        return parse_version(setuptools.__version__) >= parse_version('0.7.2')
    except Exception as exc:
        sys.stderr.write("Could not test setuptool's version: %s\n" % exc)
        return False

def main():
    install_requires = []
    extras_require = {'SSL': ['cryptography']}
    if has_environment_marker_support():
        pass
    else:
        pass

    setup(name='py2p',
          description='A python library for peer-to-peer networking',
          long_description=long_description,
          version=__version__,
          author='Gabe Appleton',
          author_email='gappleto97+development@gmail.com',
          url='https://github.com/gappleto97/p2p-project',
          license='LGPLv3',
          packages=['py2p', 'py2p.test'],
          package_dir={'py2p': 'py_src'},
          classifiers=classifiers,
          install_requires=install_requires,
          extras_require=extras_require
    )

if __name__ == "__main__":
    main()