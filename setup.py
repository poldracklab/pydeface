#!/usr/bin/env python
#
# Copyright (C) 2013-2015 Russell Poldrack <poldrack@stanford.edu>
#
# Some portions were borrowed from:
# https://github.com/mwaskom/lyman/blob/master/setup.py

import os
from setuptools import setup

DISTNAME = "pydeface"
DESCRIPTION = "pydeface: a script to remove facial structure from MRI images."
MAINTAINER = 'Russ Poldrack'
MAINTAINER_EMAIL = 'poldrack@stanford.edu'
LICENSE = 'MIT'
URL = 'http://poldracklab.org'
DOWNLOAD_URL = 'https://github.com/poldracklab/pydeface/'
VERSION = '1.1'

if os.path.exists('MANIFEST'):
    os.remove('MANIFEST')

datafiles = {'pydeface': ['data/facemask.nii.gz',
                          'data/mean_reg2mean.nii.gz']}

setup(name=DISTNAME,
      maintainer=MAINTAINER,
      maintainer_email=MAINTAINER_EMAIL,
      description=DESCRIPTION,
      license=LICENSE,
      version=VERSION,
      url=URL,
      download_url=DOWNLOAD_URL,
      packages=['pydeface'],
      package_data=datafiles,
      scripts=['scripts/pydeface.py'],
      classifiers=['Intended Audience :: Science/Research',
                   'Programming Language :: Python :: 2.7',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: POSIX',
                   'Operating System :: Unix',
                   'Operating System :: MacOS'],
      install_requires=['numpy', 'nibabel', 'nipype'],
      )
