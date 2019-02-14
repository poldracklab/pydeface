"""Utility scripts for pydeface."""

import sys
import numpy as np
from nipype.interfaces import fsl
from nipype.interfaces.io import DataSink
from nipype import Node, MapNode, Function, Workflow


def initial_checks(template=None, facemask=None, infile=None, outfile=None, force=False, applyto=None):
    """Initial sanity checks and get output filename"""
    import os
    from pkg_resources import resource_filename, Requirement
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

    # Inline function definition, because nipype
    def output_checks(infile, outfile, force):
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

    outfile = output_checks(infile, outfile, force)
    if applyto is not None:
        applyto_outfiles = [output_checks(f, None, force) for f in applyto]
    else:
        applyto_outfiles = None
    return template, facemask, outfile, applyto_outfiles


def cleanup_files(*args):
    import os
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


def deface(infile, warped_mask, outfile):
    import numpy
    import nibabel
    # multiply mask by infile and save
    infile_img = nibabel.load(infile)
    warped_mask_img = nibabel.load(warped_mask)
    try:
        outdata = infile_img.get_data().squeeze() * warped_mask_img.get_data()
    except ValueError:
        tmpdata = numpy.stack([warped_mask_img.get_data()] *
                              infile_img.get_data().shape[-1], axis=-1)
        outdata = infile_img.get_data() * tmpdata

    masked_brain = nibabel.Nifti1Image(outdata, infile_img.affine,
                                       infile_img.header)
    masked_brain.to_filename(outfile)
    print("Defaced image saved as:\n  %s" % outfile)
    return warped_mask_img


def deface_follower(applyfile, warped_mask_img, outfile):
    import nibabel
    applyfile_img = nibabel.load(applyfile)

    try:
        outdata = applyfile_img.get_data() * warped_mask_img.get_data()
    except ValueError:
        tmpdata = np.stack([warped_mask_img.get_data()] *
                           applyfile_img.get_data().shape[-1], axis=-1)
        outdata = applyfile_img.get_data() * tmpdata
    applyfile_img = nibabel.Nifti1Image(outdata, applyfile_img.affine,
                                        applyfile_img.header)
    applyfile_img.to_filename(outfile)
    print('  %s' % applyfile)


def append_follower_wf(defacewf, applyto):
    # add the applytos to the input check node
    # Doing this at the top of the workflow checks that outputs
    # don't exist before running everything
    ic_node = defacewf.get_node('initial_checks')
    ic_node.inputs.applyto = applyto

    # Grab the deface node
    deface_node = defacewf.get_node('deface')

    # Create a map node to take care of follower images
    follower = Function(inputs=['applyfile', 'warped_mask_img', 'outfile'],
                        outputs=[],
                        function=deface_follower)
    follower_node = MapNode(follower, ['applyfile', 'outfile'], 'follower')
    follower_node.inputs.applyfile = applyto

    ################ Modify defacewf connections ################
    defacewf.connect([(deface_node, follower_node, [('warped_mask_img', 'warped_mask_img')]),
                      (ic_node, follower_node, [('applyto_outfiles', 'outfile')])])

    return defacewf


def make_deface_workflow(infile=None, outfile=None, facemask=None,
                         template=None, cost='mutualinfo', force=False,
                         nocleanup=False, verbose=True, output_dir=None,
                         **kwargs):
    # Instantiate nodes and fill in inputs
    # Initial checks node
    ic_node = Node(Function(input_names=['infile', 'template',
                                         'facemask', 'outfile',
                                         'force', 'applyto'],
                            output_names=['template', 'facemask', 'outfile', 'applyto_outfiles'],
                            function=initial_checks),
                   name="initial_checks")
    ic_node.inputs.template = template
    ic_node.inputs.facemask = facemask
    ic_node.inputs.infile = infile
    ic_node.inputs.outfile = outfile
    ic_node.inputs.force = force
    ic_node.inputs.applyto = None

    # Figure out the output type for flirt based on the output file
    got_interface = Function(input_names=['outpath'],
                             output_names=['output_type'],
                             function=get_outfile_type)
    got_reg_node = Node(got_interface,
                        name='get_outfile_type_reg')
    got_reg_node.inputs.outpath = infile
    got_apply_node = Node(got_interface,
                          name='get_outfile_type_apply')
    got_apply_node.inputs.outpath = infile

    # Flirt to register template to input file
    flirt_reg = Node(fsl.FLIRT(), name='flirt_reg')
    flirt_reg.inputs.cost_func = cost
    flirt_reg.inputs.reference = infile

    # Flirt to apply the transformation to the face mask
    flirt_apply = Node(fsl.FLIRT(), name='flirt_apply')
    flirt_apply.inputs.apply_xfm = True
    flirt_apply.inputs.reference = infile

    # The deface function multiplies the infile by the warped mask
    deface_node = Node(Function(input_names=['infile',
                                             'warped_mask',
                                             'outfile'],
                                output_names=['warped_mask_img'],
                                function=deface),
                       name='deface')
    deface_node.inputs.infile = infile

    # The datasink workflow makes outputs available after the workflow completes
    datasink = Node(DataSink(), name='sinker')

    # Create the deface workflwo
    defacewf = Workflow(name='defacewf')
    defacewf.base_dir = output_dir

    ############### Connect nodes to assemble the nipype workflow #################
    defacewf.connect([(ic_node, flirt_reg, [('template', 'in_file')]),
                      (ic_node, flirt_apply, [('facemask', 'in_file')]),
                      (ic_node, deface_node, [('outfile', 'outfile')]),
                      (got_reg_node, flirt_reg, [('output_type', 'output_type')]),
                      (got_apply_node, flirt_apply, [('output_type', 'output_type')]),
                      (flirt_reg, flirt_apply, [('out_matrix_file', 'in_matrix_file')]),
                      (flirt_apply, deface_node, [('out_file', 'warped_mask')])
                      ])
    if nocleanup:
        defacewf.connect([(flirt_apply, datasink, [('out_file', 'defacing_files.@warped_mask')]),
                          (flirt_reg, datasink, [('out_file', 'defacing_files.@template_reg'),
                                                 ('out_matrix_file', 'defacing_files.@template_reg_mat')])])
    ######## End of nipype workflow assembly ########
    return defacewf
