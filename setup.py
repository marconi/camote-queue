#!/usr/bin/env python

import os
import sys
import camote

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

packages = ['camote']
requires = ['redis']

setup(
    name='camote',
    version=camote.__version__,
    description='Python based queue on top of Redis.',
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
