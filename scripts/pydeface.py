#!/usr/bin/env python
"""
deface an image using FSL
USAGE:  deface -i <filename to deface> -o [output filename]
"""

## Copyright 2011, Russell Poldrack. All rights reserved.

## Redistribution and use in source and binary forms, with or without modification, are
## permitted provided that the following conditions are met:

##    1. Redistributions of source code must retain the above copyright notice, this list of
##       conditions and the following disclaimer.

##    2. Redistributions in binary form must reproduce the above copyright notice, this list
##       of conditions and the following disclaimer in the documentation and/or other materials
##       provided with the distribution.

## THIS SOFTWARE IS PROVIDED BY RUSSELL POLDRACK ``AS IS'' AND ANY EXPRESS OR IMPLIED
## WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
## FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL RUSSELL POLDRACK OR
## CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
## CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
## SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
## ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
## NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
## ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import os
import sys
import tempfile
import subprocess
import inspect
import argparse
import nibabel
from scipy import ndimage as nd
from nipype.interfaces import fsl
from pkg_resources import resource_filename, Requirement


def run_shell_cmd(cmd,cwd=[]):
    """
    Run a command in the shell using Popen
    """
    if cwd:
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, cwd=cwd)
    else:
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    for line in process.stdout:
        print(line.strip())

    process.wait()


def main():

    # T1w template and face mask locations
    T1w_template = resource_filename(Requirement.parse("pydeface"), 'pydeface/data/T1w_template.nii.gz')
    facemask = resource_filename(Requirement.parse("pydeface"), "pydeface/data/facemask.nii.gz")


    try:
        assert os.path.exists(T1w_template)
    except:
        raise Exception('*** Missing template : %s'%T1w_template)

    try:
        assert os.path.exists(facemask)
    except:
        raise Exception('*** Missing facemask : %s'%facemask)

    # Check that FSLDIR is set
    if os.environ.get('FSLDIR'):
        FSLDIR = os.environ['FSLDIR']
    else:
        print('FSL must be installed and FSLDIR environment variable must be defined')
        sys.exit(2)

    # Command line argument parser
    parser = argparse.ArgumentParser(description='Remove facial structure from MRI images')
    parser.add_argument('-i', '--infile', required=True, help='T1w input image')
    parser.add_argument('-o', '--outfile', required=False, help='Defaced output image [<infile>_defaced.nii.gz]')
    parser.add_argument('-s', '--scalefactor', required=False, help='Voxelation scale factor [8.0]')

    # Parse command line arguments
    args = parser.parse_args()

    # Input T1w image filename
    T1w_fname = args.infile

    # Create output filename if not supplied
    if args.outfile:
        T1w_defaced_fname = args.outfile
    else:
        T1w_defaced_fname = T1w_fname.replace('.nii.gz','_defaced.nii.gz')

    if args.scalefactor:
        vox_sf = float(args.scalefactor)
    else:
        vox_sf = 8.0

    # Check if output file already exists
    if os.path.isfile(T1w_defaced_fname):
        print('%s already exists - remove it first' % T1w_defaced_fname)
        sys.exit(1)

    # Temporary template to individual affine transform matrix
    _, temp2ind_mat_fname = tempfile.mkstemp()
    temp2ind_mat_fname += '.mat'

    # Temporal face mask in individual space
    _, indmask_fname_fname = tempfile.mkstemp()
    indmask_fname_fname += '.nii.gz'

    # Dummy output data
    _, dummy_img_fname = tempfile.mkstemp()
    _, dummy_mat_fname = tempfile.mkstemp()

    print('Defacing %s' % T1w_fname)

    # Register template to infile
    print('Registering template to individual space')
    flirt = fsl.FLIRT()
    flirt.inputs.cost_func='mutualinfo'
    flirt.inputs.in_file = T1w_template
    flirt.inputs.out_matrix_file = temp2ind_mat_fname
    flirt.inputs.reference = T1w_fname
    flirt.inputs.out_file = dummy_img_fname
    flirt.run()

    # Affine transform facemask to infile
    print('Resampling face mask to individual space')
    flirt = fsl.FLIRT()
    flirt.inputs.in_file = facemask
    flirt.inputs.in_matrix_file = temp2ind_mat_fname
    flirt.inputs.apply_xfm = True
    flirt.inputs.reference = T1w_fname
    flirt.inputs.out_file = indmask_fname_fname
    flirt.inputs.out_matrix_file = dummy_mat_fname
    flirt.run()

    # Load T1w input image
    print('Loading T1w image : %s' % T1w_fname)
    T1w_nii = nibabel.load(T1w_fname)
    T1w_img = T1w_nii.get_data()

    # Voxelate T1w image
    # 1. Cubic downsample
    # 2. Nearest neighbor upsample
    print('Voxelating T1w image : scale factor %0.1f' % vox_sf)
    print('  Spline downsampling')
    T1w_vox_img = nd.interpolation.zoom(T1w_img, zoom=1.0/vox_sf, order=3)
    print('  Nearest neighbor upsampling')
    T1w_vox_img = nd.interpolation.zoom(T1w_vox_img, zoom=vox_sf, order=0)

    # Load individual space face mask
    indmask_nii = nibabel.load(indmask_fname_fname)
    indmask_img = indmask_nii.get_data()

    # Replace face area with voxelated version
    # Note that the face mask is 0 in the face region, 1 elsewhere.
    print('Anonymizing face area')
    T1w_defaced_img = T1w_img * indmask_img + T1w_vox_img * (1 - indmask_img)

    # Save defaced image
    print('Saving defaced image : %s' % T1w_defaced_fname)
    outfile_img = nibabel.Nifti1Image(T1w_defaced_img, T1w_nii.get_affine(), T1w_nii.get_header())
    outfile_img.to_filename(T1w_defaced_fname)

    # Cleanup temporary files
    print('Cleaning up')
    os.remove(temp2ind_mat_fname)
    os.remove(indmask_fname_fname)
    os.remove(dummy_img_fname)
    os.remove(dummy_mat_fname)


if __name__ == "__main__":
    main()
