import pydeface.utils as pdu
from shutil import which
import tempfile
import pytest
from pathlib import Path
import urllib.request
from shutil import copyfile


def test_cleanup_files():
    files = []
    for p in range(3):
        files.append(tempfile.mkstemp()[1])
    pdu.cleanup_files(files[0])
    pdu.cleanup_files(*files[1:])
    # should not fail if files do not exist
    pdu.cleanup_files(*files)


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
        follow_img = (
            Path(__file__).
            parent.parent.
            joinpath(
                'tests',
                'data',
                'ds000031_sub-01_ses-006_run-001_T1w_follower.nii.gz').as_posix())
        # From https://stackoverflow.com/a/7244263
        data_url = 'https://openneuro.org/crn/datasets/ds000031/files/sub-01:ses-006:anat:sub-01_ses-006_run-001_T1w.nii.gz'
        urllib.request.urlretrieve(data_url, test_img)
        copyfile(test_img, follow_img)
        defacewf = pdu.make_deface_workflow(test_img,nocleanup=False,force=True)
        defacewf = pdu.append_follower_wf(defacewf, [follow_img])
        deface_res = defacewf.run()
        pdu.cleanup_files(test_img, follow_img)
    else:
        pytest.skip("no fsl to run defacing.")
