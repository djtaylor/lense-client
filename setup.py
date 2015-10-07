#!/usr/bin/python
from setuptools import setup, find_packages

# Import the module version
from lense.client import __version__

# Run the setup
setup(
    name             = 'lense-client',
    version          = __version__,
    description      = 'Client Python libraries and scripts for the Lense API engine',
    long_description = open('DESCRIPTION.rst').read(),
    author           = 'David Taylor',
    author_email     = 'djtaylor13@gmail.com',
    url              = 'http://github.com/djtaylor/lense-client',
    license          = 'GPLv3',
    install_requires = ['lense-common>=0.1.1'],
    packages         = find_packages(),
    keywords         = 'lense module library client',
    classifiers      = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Terminals',
    ],
    entry_points = {
        'console_scripts': [
            'lense = lense.client.interface:cli',
        ],
    },
    exclude_package_data = {'': ['lense/__init__.py']}
)