#! /usr/bin/env python
#
# Copyright (C) 2013-2015 Russell Poldrack <poldrack@stanford.edu>
# some portions borrowed from https://github.com/mwaskom/lyman/blob/master/setup.py


descr = """myconnectome: a package to implement analyses for the myconnectome project"""

import os
from setuptools import setup

DISTNAME="myconnectome"
DESCRIPTION=descr
MAINTAINER='Russ Poldrack'
MAINTAINER_EMAIL='poldrack@stanford.edu'
LICENSE='MIT'
URL='http://myconnectome.org'
DOWNLOAD_URL='https://github.com/poldrack/myconnectome/'
VERSION='0.9.0.dev'

def check_dependencies():

    # Just make sure dependencies exist, I haven't rigorously
    # tested what the minimal versions that will work are
    needed_deps = ["IPython", "numpy", "scipy", "matplotlib",
                   "sklearn", "statsmodels", "networkx",
                   "gtf_to_genes","pandas","nilearn",
		   "nibabel","boto","suds","mygene"]
    missing_deps = []
    for dep in needed_deps:
        try:
            __import__(dep)
        except ImportError:
            missing_deps.append(dep)

    if missing_deps:
        missing = (", ".join(missing_deps)
                   .replace("sklearn", "scikit-learn"))
        raise ImportError("Missing dependencies: %s" % missing)

if __name__ == "__main__":

    if os.path.exists('MANIFEST'):
        os.remove('MANIFEST')

    import sys
    if not (len(sys.argv) >= 2 and ('--help' in sys.argv[1:] or
            sys.argv[1] in ('--help-commands',
                            '--version',
                            'egg_info',
                            'clean'))):
        check_dependencies()

    setup(name=DISTNAME,
        maintainer=MAINTAINER,
        maintainer_email=MAINTAINER_EMAIL,
        description=DESCRIPTION,
        license=LICENSE,
        version=VERSION,
        url=URL,
        download_url=DOWNLOAD_URL,
        #install_requires=["moss>=0.3.3"],
        packages=['myconnectome', 'myconnectome.tests',
                  'myconnectome.diffusion', 'myconnectome.rsfmri',
                  'myconnectome.utils', 'myconnectome.taskfmri',
                  'myconnectome.timeseries','myconnectome.rnaseq',
                  'myconnectome.metabolomics'],
#        scripts=['scripts/run_fmri.py', 'scripts/run_group.py',
#                 'scripts/run_warp.py', 'scripts/setup_project.py',
#                 'scripts/make_masks.py', 'scripts/anatomy_snapshots.py',
#                 'scripts/surface_snapshots.py'],
        classifiers=[
                     'Intended Audience :: Science/Research',
                     'Programming Language :: Python :: 2.7',
                     'License :: OSI Approved :: BSD License',
                     'Operating System :: POSIX',
                     'Operating System :: Unix',
                     'Operating System :: MacOS'],
    )
