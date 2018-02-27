"""Utility scripts for pydeface."""

import os
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




def deface_image(infile=None, outfile=None, facemask=None,
                 template=None, cost='other', force=False, forcecleanup=False,
                 verbose=True, **kwargs):
    if not infile:
        raise ValueError("infile must be specified")

    template, facemask = initial_checks(template, facemask)
    outfile = output_checks(infile, outfile, force)

    # temporary files
    _, template_reg_mat = tempfile.mkstemp()
    template_reg_mat = template_reg_mat + '.mat'
    _, warped_mask = tempfile.mkstemp()
    warped_mask = warped_mask + '.nii.gz'
    if verbose:
        print("Temporary files:\n  %s\n  %s" % (template_reg_mat, warped_mask))
    _, template_reg = tempfile.mkstemp()
    _, warped_mask_mat = tempfile.mkstemp()

    print('Defacing...\n  %s' % infile)

    # register template to infile
    flirt = fsl.FLIRT()
    flirt.inputs.cost_func = cost
    flirt.inputs.in_file = template
    flirt.inputs.out_matrix_file = template_reg_mat
    flirt.inputs.out_file = template_reg
    flirt.inputs.reference = infile
    flirt.run()

    # warp facemask to infile
    flirt = fsl.FLIRT()
    flirt.inputs.in_file = facemask
    flirt.inputs.in_matrix_file = template_reg_mat
    flirt.inputs.apply_xfm = True
    flirt.inputs.reference = infile
    flirt.inputs.out_file = warped_mask
    flirt.inputs.out_matrix_file = warped_mask_mat
    flirt.run()

    # multiply mask by infile and save
    infile_img = load(infile)
    warped_mask_img = load(warped_mask)
    try:
        outdata = infile_img.get_data().squeeze() * warped_mask_img.get_data()
    except ValueError:
        tmpdata = np.stack([warped_mask_img.get_data()] *
                           infile_img.get_data().shape[-1], axis=-1)
        outdata = infile_img.get_data() * tmpdata

    masked_brain = Nifti1Image(outdata, infile_img.get_affine(),
                               infile_img.get_header())
    masked_brain.to_filename(outfile)
    print("Defaced image saved as:\n  %s" % outfile)

    if forcecleanup:
        print('Cleaning up')
        os.remove(warped_mask)
        os.remove(template_reg)
        os.remove(template_reg_mat)
        return warped_mask_img
    else:
        return warped_mask_img,warped_mask, template_reg, template_reg_mat


