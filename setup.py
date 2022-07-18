#!/usr/bin/env python
"""Developer notes

- Prepare for pypi:
python setup.py sdist

- Upload to pypi test server to check:
twine upload --repository-url https://test.pypi.org/legacy/ dist/*

- Use testpypi with pip:
pip install --index-url https://test.pypi.org/simple/ pydeface

- Upload to pypi
twine upload dist/*
"""


import os
from setuptools import setup

VERSION = '2.0.2'

# read the contents of README.md
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    LONG_DESCRIPTION = f.read()

if os.path.exists('MANIFEST'):
    os.remove('MANIFEST')

datafiles = {'pydeface': ['data/facemask.nii.gz',
                          'data/mean_reg2mean.nii.gz']}

setup(name='pydeface',
      maintainer='Russ Poldrack',
      maintainer_email='poldrack@stanford.edu',
      description='A script to remove facial structure from MRI images.',
      long_description=LONG_DESCRIPTION,
      long_description_content_type='text/markdown',
      license='MIT',
      version=VERSION,
      url='http://poldracklab.org',
      download_url=('https://github.com/poldracklab/pydeface/archive/'
                    + VERSION + '.tar.gz'),
      packages=['pydeface'],
      package_data=datafiles,
      classifiers=['Intended Audience :: Science/Research',
                   'Programming Language :: Python :: 3.7',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: POSIX',
                   'Operating System :: Unix',
                   'Operating System :: MacOS'],
      install_requires=[
          'numpy',
          'nibabel',
          'nipype',
          'setuptools',  # needed at runtime (for the pkg_resources module)
      ],
      entry_points={
            'console_scripts': [
                'pydeface = pydeface.__main__:main'
                ]},
      )
