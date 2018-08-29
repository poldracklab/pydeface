#!/usr/bin/env python
"""Defacing utility for MRI images."""

# Copyright 2011, Russell Poldrack. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    1. Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#    2. Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY RUSSELL POLDRACK ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL RUSSELL POLDRACK OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import argparse
from nibabel import load, Nifti1Image
from pkg_resources import require
import pydeface.utils as pdu
import sys
import shutil


def is_interactive():
    """Return True if all in/outs are tty"""
    # TODO: check on windows if hasattr check would work correctly and add value:
    return sys.stdin.isatty() and sys.stdout.isatty() and sys.stderr.isatty()


def setup_exceptionhook():
    """
    Overloads default sys.excepthook with our exceptionhook handler.

    If interactive, our exceptionhook handler will invoke pdb.post_mortem;
    if not interactive, then invokes default handler.
    """
    def _pdb_excepthook(type, value, tb):
        if is_interactive():
            import traceback
            import pdb
            traceback.print_exception(type, value, tb)
            # print()
            pdb.post_mortem(tb)
        else:
            lgr.warn(
                "We cannot setup exception hook since not in interactive mode")

    sys.excepthook = _pdb_excepthook


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
        "--force", action='store_true',
        help="Force to rewrite the output even if it exists.")

    parser.add_argument(
        '--applyto', nargs='+', required=False, metavar='',
        help="Apply the created face mask to other images. Can take multiple "
             "arguments.")

    parser.add_argument(
        "--cost", metavar='mutualinfo', required=False, default='mutualinfo',
        help="FSL-FLIRT cost function. Default is 'mutualinfo'.")

    parser.add_argument(
        "--template", metavar='path', required=False,
        help=("Optional template image that will be used as the registration "
              "target instead of the default."))

    parser.add_argument(
        "--facemask", metavar='path', required=False,
        help="Optional face mask image that will be used instead of the "
             "default.")

    parser.add_argument(
        "--nocleanup", action='store_true',
        help="Do not cleanup temporary files. Off by default.")

    parser.add_argument(
        "--verbose", action='store_true',
        help="Show additional status prints. Off by default.")

    parser.add_argument('--debug', action='store_true', dest='debug',
                        help='Do not catch exceptions and show exception '
                        'traceback (Drop into pdb debugger).')

    welcome_str = 'pydeface ' + require("pydeface")[0].version
    welcome_decor = '-' * len(welcome_str)
    print(welcome_decor + '\n' + welcome_str + '\n' + welcome_decor)

    args = parser.parse_args()
    if args.debug:
        setup_exceptionhook()

    warped_mask_img, warped_mask, template_reg, template_reg_mat =\
        pdu.deface_image(**vars(args))

    # apply mask to other given images
    if args.applyto is not None:
        print("Defacing mask also applied to:")
        for applyfile in args.applyto:
            applyfile_img = load(applyfile)
            outdata = applyfile_img.get_data() * warped_mask_img.get_data()
            applyfile_img = Nifti1Image(outdata, applyfile_img.get_affine(),
                                        applyfile_img.get_header())
            outfile = pdu.output_checks(applyfile)
            applyfile_img.to_filename(outfile)
            print('  %s' % applyfile)

    if not args.nocleanup:
        pdu.cleanup_files(warped_mask, template_reg, template_reg_mat)
    else:
        unclean_mask = args.infile.replace('.gz', '').replace('.nii','_pydeface_mask.nii.gz')
        unclean_mat = args.infile.replace('.gz','').replace('.nii','_pydeface.mat')
        shutil.move(warped_mask, unclean_mask)
        shutil.move(template_reg_mat, unclean_mat)

    print('Finished.')


if __name__ == "__main__":
    main()
