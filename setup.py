#! /usr/bin/env python3

import setuptools

with open('README.md') as fh:
    long_description = fh.read()

setuptools.setup(
    name='pysqlgrid',
    version='1.0.1',
    author='REX Engineering',
    author_email='jhanley_pysqlgrid@s6.sector6.net',
    description='Frontend for displaying SQL query results on the web.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/jhanley634/pysqlgrid',
    packages=setuptools.find_packages(),
    classifiers=(
        'Environment :: Web Environment',
        'Framework :: Flask',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Database :: Front-Ends',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Office/Business :: Financial :: Spreadsheet',
        'Topic :: Software Development :: User Interfaces',
    ),
)
