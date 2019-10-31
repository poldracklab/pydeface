#!/usr/bin/env python
#
# Copyright (C) 2013-2015 Russell Poldrack <poldrack@stanford.edu>
#
# Some portions were borrowed from:
# https://github.com/mwaskom/lyman/blob/master/setup.py
# and:
# https://chriswarrick.com/blog/2014/09/15/python-apps-the-right-way-entry_points-and-scripts/

import os
from setuptools import setup

VERSION = '2.0.0'

if os.path.exists('MANIFEST'):
    os.remove('MANIFEST')

datafiles = {'pydeface': ['data/facemask.nii.gz',
                          'data/mean_reg2mean.nii.gz']}

setup(name='pydeface',
      maintainer='Russ Poldrack',
      maintainer_email='poldrack@stanford.edu',
      description='A script to remove facial structure from MRI images.',
      license='MIT',
      version=VERSION,
      url='http://poldracklab.org',
      download_url=('https://github.com/poldracklab/pydeface/archive'
                    + VERSION + '.tar.gz')
      packages=['pydeface'],
      package_data=datafiles,
      classifiers=['Intended Audience :: Science/Research',
                   'Programming Language :: Python :: 3.7',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: POSIX',
                   'Operating System :: Unix',
                   'Operating System :: MacOS'],
      install_requires=['numpy', 'nibabel', 'nipype'],
      entry_points={
            'console_scripts': [
                'pydeface = pydeface.__main__:main'
                ]},
      )
