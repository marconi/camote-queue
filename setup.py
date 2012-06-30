#!/usr/bin/env python

import os
import sys
import camote

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist register upload')
    sys.exit()

packages = ['camote']
requires = ['redis==2.4.13']

setup(
    name='camote-queue',
    version=camote.__version__,
    description='Redis based queue that supports fetching job position.',
    long_description=open('README.rst').read() + '\n\n' +
                     open('HISTORY.rst').read(),
    author='Marconi Moreto',
    author_email='caketoad@gmail.com',
    url='https://github.com/marconi/camote-queue',
    packages=packages,
    zip_safe=False,
    package_data={'': ['LICENSE']},
    include_package_data=True,
    install_requires=requires,
    license=open("LICENSE").read(),
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ),
)
