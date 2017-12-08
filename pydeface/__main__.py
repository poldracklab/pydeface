#!/usr/bin/env python
"""Defacing utility for MRI images."""

import argparse
import os
import tempfile
from nipype.interfaces import fsl
from nibabel import load, Nifti1Image
from pkg_resources import resource_filename, Requirement, require
from pydeface.utils import initial_checks, check_output_path


def main():
    """Command line call argument parsing."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'infile', metavar='path',
        help="Path to input nifti.")

    parser.add_argument(
        "--outfile", metavar='path', required=False,
        help="If not provided adds '_defaced' suffix.")

    parser.add_argument(
        '--applyto', nargs='+', required=False, metavar='path',
        help='Apply the created face mask to other images.')

    parser.add_argument(
        "--force", action='store_true',
        help="Force to rewrite the output even if it exists.")

    parser.add_argument(
        "--nocleanup", action='store_true',
        help="Do not cleanup temporary files.")

    parser.add_argument(
        "--verbose", action='store_true',
        help="Show additional status prints.")

    welcome_str = 'pydeface ' + require("pydeface")[0].version
    welcome_decor = '-' * len(welcome_str)
    print(welcome_decor + '\n' + welcome_str + '\n' + welcome_decor)

    template = resource_filename(Requirement.parse("pydeface"),
                                 "pydeface/data/mean_reg2mean.nii.gz")
    facemask = resource_filename(Requirement.parse("pydeface"),
                                 "pydeface/data/facemask.nii.gz")

    initial_checks(template, facemask)
    args = parser.parse_args()
    infile = args.infile
    outfile = check_output_path(infile, args.outfile, args.force)

    # temporary files
    _, tmpmat = tempfile.mkstemp()
    tmpmat = tmpmat + '.mat'
    _, tmpfile = tempfile.mkstemp()
    tmpfile = tmpfile + '.nii.gz'
    if args.verbose:
        print(tmpmat)
        print(tmpfile)
    _, tmpfile2 = tempfile.mkstemp()
    _, tmpmat2 = tempfile.mkstemp()

    print('Defacing...\n  %s' % args.infile)

    # register template to infile
    flirt = fsl.FLIRT()
    flirt.inputs.cost_func = 'mutualinfo'
    flirt.inputs.in_file = template
    flirt.inputs.out_matrix_file = tmpmat
    flirt.inputs.out_file = tmpfile2
    flirt.inputs.reference = infile
    flirt.run()

    # warp facemask to infile
    flirt = fsl.FLIRT()
    flirt.inputs.in_file = facemask
    flirt.inputs.in_matrix_file = tmpmat
    flirt.inputs.apply_xfm = True
    flirt.inputs.reference = infile
    flirt.inputs.out_file = tmpfile
    flirt.inputs.out_matrix_file = tmpmat2
    flirt.run()

    # multiply mask by infile and save
    infile_img = load(infile)
    tmpfile_img = load(tmpfile)
    outdata = infile_img.get_data() * tmpfile_img.get_data()
    outfile_img = Nifti1Image(outdata, infile_img.get_affine(),
                              infile_img.get_header())
    outfile_img.to_filename(outfile)
    print('Defaced input saved as:\n  %s' % outfile)

    # apply mask to other given images
    if args.applyto is not None:
        print("Defacing mask also applied to:")
        for applyfile in args.applyto:
            applyfile_img = load(applyfile)
            outdata = applyfile_img.get_data() * tmpfile_img.get_data()
            applyfile_img = Nifti1Image(outdata, applyfile_img.get_affine(),
                                        applyfile_img.get_header())
            outfile_img.to_filename(applyfile)
            print('  %s' % applyfile)

    if args.nocleanup:
        pass
    else:
        os.remove(tmpfile)
        os.remove(tmpfile2)
        os.remove(tmpmat)

    print('Finished.')


if __name__ == "__main__":
    main()
