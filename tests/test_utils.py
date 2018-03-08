import pydeface.utils as pdu
from shutil import which
import tempfile
import os
import pytest
from pathlib import Path
TESTS_DATA_PATH = Path(__file__,
    '..', 'tests', 'data',
    'ds_000031_sub-01_ses-006_run-001_T1w.nii.gz')



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
        test_img = (
            Path(__file__).
            parent.parent.
            joinpath(
                'tests',
                'data',
                'ds000031_sub-01_ses-006_run-001_T1w.nii.gz').as_posix())
        pdu.deface_image(test_img,forcecleanup=True,force=True)
        pdu.cleanup_files(test_img)


    else:
        pytest.skip("no fsl to run defacing.")

