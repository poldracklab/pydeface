import pydeface.utils as pdu
from shutil import which
import tempfile
import os
import pytest
from pathlib import Path


def test_cleanup_files():
    files = []
    for p in range(3):
        files.append(tempfile.mkstemp()[1])
    pdu.cleanup_files(files[0])
    pdu.cleanup_files(*files[1:])
    # should not fail if files do not exist
    pdu.cleanup_files(*files)


def test_generate_tmpfiles():
    files = pdu.generate_tmpfiles()
    for f in files:
        assert os.path.exists(f)
        os.remove(f)


def test_get_outfile_type():
    assert pdu.get_outfile_type('path.nii.gz') == 'NIFTI_GZ'
    assert pdu.get_outfile_type('path.nii') == 'NIFTI'
    with pytest.raises(ValueError):
        pdu.get_outfile_type('path.suffix')


def test_deface_image():
    if which('fsl'):
        # Piece together test data path
        test_img_name = 'ds000031_sub-01_ses-006_run-001_T1w'
        pydeface_path = Path(__file__).parent.parent
        test_img_path = os.path.join(
            pydeface_path, 'tests', 'data',
            "{}.nii.gz".format(test_img_name))

        # Run pydeface
        pdu.deface_image(test_img_path, forcecleanup=True, force=True)

        # Cleanup output nifti to not mistakenly push to repo
        test_img_outpath = os.path.join(
        pydeface_path, 'tests', 'data',
        "{}_defaced.nii.gz".format(test_img_name))
        pdu.cleanup_files(test_img_outpath)

    else:
        pytest.skip("No FSL to run defacing.")
