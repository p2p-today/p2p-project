# from distutils.core import setup
from setuptools import setup
from py_src import __version__

setup(name='py2p',
      description='A python library for peer-to-peer networking',
      version=__version__,
      author='Gabe Appleton',
      author_email='gappleto97+development@gmail.com',
      url='https://github.com/gappleto97/p2p-project',
      license='LGPLv3',
      packages=['py2p', 'py2p.test'],
      package_dir={'py2p': 'py_src'},
      classifiers=['Development Status :: 3 - Alpha',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
                   'Programming Language :: Python :: 2',
                   'Programming Language :: Python :: 2.6',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.3',
                   'Programming Language :: Python :: 3.4',
                   'Programming Language :: Python :: 3.5',
                   'Programming Language :: Python',
                   'Programming Language :: JavaScript',
                   'Operating System :: OS Independent',
                   'Topic :: Communications',
                   'Topic :: Internet'])