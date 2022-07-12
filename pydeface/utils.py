"""Utility scripts for pydeface."""

import os
import shutil
import sys
from pkg_resources import resource_filename, Requirement
import tempfile
import numpy as np
from nipype.interfaces import fsl
from nibabel import load, Nifti1Image


def initial_checks(template=None, facemask=None):
    """Initial sanity checks."""
    if template is None:
        template = resource_filename(Requirement.parse("pydeface"),
                                     "pydeface/data/mean_reg2mean.nii.gz")
    if facemask is None:
        facemask = resource_filename(Requirement.parse("pydeface"),
                                     "pydeface/data/facemask.nii.gz")

    if not os.path.exists(template):
        raise Exception('Missing template: %s' % template)
    if not os.path.exists(facemask):
        raise Exception('Missing face mask: %s' % facemask)

    if 'FSLDIR' not in os.environ:
        raise Exception("FSL must be installed and "
                        "FSLDIR environment variable must be defined.")
        sys.exit(2)
    return template, facemask


def output_checks(infile, outfile=None, force=False):
    """Determine output file name."""
    if force is None:
        force = False
    if outfile is None:
        outfile = infile.replace('.nii', '_defaced.nii')

    if os.path.exists(outfile) and force:
        print('Previous output will be overwritten.')
    elif os.path.exists(outfile):
        raise Exception("%s already exists. Remove it first or use '--force' "
                        "flag to overwrite." % outfile)
    else:
        pass
    return outfile


def generate_tmpfiles(verbose=True):
    _, template_reg_mat = tempfile.mkstemp(suffix='.mat')
    _, warped_mask = tempfile.mkstemp(suffix='.nii.gz')
    if verbose:
        print("Temporary files:\n  %s\n  %s" % (template_reg_mat, warped_mask))
    _, template_reg = tempfile.mkstemp(suffix='.nii.gz')
    _, warped_mask_mat = tempfile.mkstemp(suffix='.mat')
    return template_reg, template_reg_mat, warped_mask, warped_mask_mat


def cleanup_files(*args):
    print("Cleaning up...")
    for p in args:
        if os.path.exists(p):
            os.remove(p)


def get_outfile_type(outpath):
    # Returns fsl output type for passing to fsl's flirt
    if outpath.endswith('nii.gz'):
        return 'NIFTI_GZ'
    elif outpath.endswith('nii'):
        return 'NIFTI'
    else:
        raise ValueError('outfile path should be have .nii or .nii.gz suffix')


def deface_image(infile=None, outfile=None, facemask=None,
                 template=None, cost='mutualinfo', force=False,
                 forcecleanup=False, verbose=True, **kwargs):
    if not infile:
        raise ValueError("infile must be specified")
    if shutil.which('fsl') is None:
        raise EnvironmentError("fsl cannot be found on the path")

    template, facemask = initial_checks(template, facemask)
    outfile = output_checks(infile, outfile, force)
    template_reg, template_reg_mat, warped_mask, warped_mask_mat = generate_tmpfiles()

    print('Defacing...\n  %s' % infile)
    # register template to infile
    outfile_type = get_outfile_type(template_reg)
    flirt = fsl.FLIRT()
    flirt.inputs.cost_func = cost
    flirt.inputs.in_file = template
    flirt.inputs.out_matrix_file = template_reg_mat
    flirt.inputs.out_file = template_reg
    flirt.inputs.output_type = outfile_type
    flirt.inputs.reference = infile
    flirt.run()

    outfile_type = get_outfile_type(warped_mask)
    # warp facemask to infile
    flirt = fsl.FLIRT()
    flirt.inputs.in_file = facemask
    flirt.inputs.in_matrix_file = template_reg_mat
    flirt.inputs.apply_xfm = True
    flirt.inputs.reference = infile
    flirt.inputs.out_file = warped_mask
    flirt.inputs.output_type = outfile_type
    flirt.inputs.out_matrix_file = warped_mask_mat
    flirt.run()

    # multiply mask by infile and save
    infile_img = load(infile)
    infile_data = np.asarray(infile_img.dataobj)
    warped_mask_img = load(warped_mask)
    warped_mask_data = np.asarray(warped_mask_img.dataobj)
    try:
        outdata = infile_data.squeeze() * warped_mask_data
    except ValueError:
        tmpdata = np.stack(warped_mask_data * infile_img.shape[-1], axis=-1)
        outdata = infile_data * tmpdata

    masked_brain = Nifti1Image(outdata, infile_img.affine, infile_img.header)
    masked_brain.to_filename(outfile)
    print("Defaced image saved as:\n  %s" % outfile)

    if forcecleanup:
        cleanup_files(warped_mask, template_reg, template_reg_mat)
        return warped_mask_img
    else:
        return warped_mask_img, warped_mask, template_reg, template_reg_mat
