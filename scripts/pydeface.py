#!/usr/bin/env python
""" deface an image using FSL
USAGE:  deface <filename to deface> <optional: outfilename>
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



import nibabel
import os,sys
import numpy as N
import tempfile
import subprocess
import inspect
from nipype.interfaces import fsl
from pkg_resources import resource_filename,Requirement

def run_shell_cmd(cmd,cwd=[]):
    """ run a command in the shell using Popen
    """
    if cwd:
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,cwd=cwd)
    else:
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    for line in process.stdout:
             print line.strip()
    process.wait()

def usage():
    """ print the docstring and exit"""
    sys.stdout.write(__doc__)
    sys.exit(2)


def main():
    cleanup=True
    verbose=False
    scriptdir=os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) # script directory

    template=resource_filename(Requirement.parse("pydeface"), 'pydeface/data/mean_reg2mean.nii.gz')
    facemask=resource_filename(Requirement.parse("pydeface"), "pydeface/data/facemask.nii.gz")

    try:
        assert os.path.exists(facemask)
    except:
        raise Exception('missing facemask: %s'%facemask)

    try:
        assert os.path.exists(template)
    except:
        raise Exception('missing template: %s'%template)



    if len(sys.argv)<2:
        usage()
        sys.exit(2)
    else:
        infile=sys.argv[1]

    if len(sys.argv)>2:
        outfile=sys.argv[2]
    else:
        outfile=infile.replace('.nii.gz','_defaced.nii.gz')
    try:
        assert not os.path.exists(outfile)
    except:
        raise Exception('%s already exists, remove it first'%outfile)

    if os.environ.has_key('FSLDIR'):
        FSLDIR=os.environ['FSLDIR']
    else:
        print 'FSL must be installed and FSLDIR environment variable must be defined'
        sys.exit(2)


    foo,tmpmat=tempfile.mkstemp()
    tmpmat=tmpmat+'.mat'
    foo,tmpfile=tempfile.mkstemp()
    tmpfile=tmpfile+'.nii.gz'
    if verbose:
        print tmpmat
        print tmpfile
    foo,tmpfile2=tempfile.mkstemp()
    foo,tmpmat2=tempfile.mkstemp()

    print 'defacing',infile
    # register template to infile

    flirt=fsl.FLIRT()
    flirt.inputs.cost_func='mutualinfo'
    flirt.inputs.in_file=template
    flirt.inputs.out_matrix_file=tmpmat
    flirt.inputs.out_file=tmpfile2
    flirt.inputs.reference=infile
    flirt.run()

    # warp facemask to infile
    flirt=fsl.FLIRT()
    flirt.inputs.in_file=facemask
    flirt.inputs.in_matrix_file=tmpmat
    flirt.inputs.apply_xfm=True
    flirt.inputs.reference=infile
    flirt.inputs.out_file=tmpfile
    flirt.inputs.out_matrix_file=tmpmat2
    flirt.run()

    # multiply mask by infile and save

    infile_img=nibabel.load(infile)
    tmpfile_img=nibabel.load(tmpfile)
    outdata=infile_img.get_data()*tmpfile_img.get_data()
    outfile_img=nibabel.Nifti1Image(outdata,infile_img.get_affine(),infile_img.get_header())
    outfile_img.to_filename(outfile)

    if cleanup:
        os.remove(tmpfile)
        os.remove(tmpfile2)
        os.remove(tmpmat)

if __name__ == "__main__":
    main()
