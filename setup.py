#!/usr/bin/python
import lense.client as lense_client
from setuptools import setup, find_packages

# Module version / long description
version = lense_client.__version__
long_desc = open('DESCRIPTION.rst').read()

# Run the setup
setup(
    name='lense-client',
    version=version,
    description='Lense API platform client libraries',
    long_description=long_desc,
    author='David Taylor',
    author_email='djtaylor13@gmail.com',
    url='http://github.com/djtaylor/lense-client',
    license='GPLv3',
    packages=find_packages(),
    keywords='lense api client platform engine',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Terminals',
    ],
    install_requires = [
        'lense-common>=0.1'
    ],
    entry_points = {
        'console_scripts': [
            'lense = lense.client.interface:cli',
        ],
    }
)