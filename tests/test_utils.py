import os
import tempfile
from pathlib import Path
from shutil import which

import nibabel as nib
import numpy as np
import pytest

import pydeface.utils as pdu


def _make_flirt_stub(reference_shape3d):
    """Build a FLIRT replacement writing a 3D mask, so FSL is not needed."""

    class StubInputs:
        pass

    class StubFLIRT:
        def __init__(self):
            self.inputs = StubInputs()

        def run(self):
            out = getattr(self.inputs, 'out_file', None)
            if out is not None:
                data = np.ones(reference_shape3d, dtype=np.int16)
                data[0, 0, 0] = 0
                nib.Nifti1Image(data, np.eye(4)).to_filename(out)
            mat = getattr(self.inputs, 'out_matrix_file', None)
            if mat is not None:
                with open(mat, 'w') as fh:
                    fh.write('1 0 0 0\n0 1 0 0\n0 0 1 0\n0 0 0 1\n')
            return self

    return StubFLIRT


def test_cleanup_files():
    files = [tempfile.mkstemp()[1] for p in range(3)]
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


def test_deface_image_requires_flirt(monkeypatch, tmp_path):
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    monkeypatch.setenv('PATH', str(bin_dir))

    with pytest.raises(OSError, match='flirt'):
        pdu.deface_image('input.nii.gz')


def test_deface_image_accepts_flirt_without_fsl(monkeypatch, tmp_path):
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    flirt = bin_dir / 'flirt'
    flirt.write_text('#!/bin/sh\nexit 0\n')
    flirt.chmod(0o755)
    monkeypatch.setenv('PATH', str(bin_dir))
    monkeypatch.delenv('FSLDIR', raising=False)

    with pytest.raises(Exception, match='FSLDIR'):
        pdu.deface_image('input.nii.gz')


def test_deface_image():
    if which('fsl'):
        # Piece together test data path
        test_img_name = 'ds000031_sub-01_ses-006_run-001_T1w'
        pydeface_path = Path(__file__).parent.parent
        test_img_path = os.path.join(
            pydeface_path, 'tests', 'data', f'{test_img_name}.nii.gz'
        )

        # Run pydeface
        pdu.deface_image(test_img_path, forcecleanup=True, force=True)

        # Cleanup output nifti to not mistakenly push to repo
        test_img_outpath = os.path.join(
            pydeface_path, 'tests', 'data', f'{test_img_name}_defaced.nii.gz'
        )
        pdu.cleanup_files(test_img_outpath)

    else:
        pytest.skip('No FSL to run defacing.')


@pytest.mark.parametrize('shape3d', [(6, 7, 8), (3, 4, 5)])
def test_deface_image_multivolume(tmp_path, monkeypatch, shape3d):
    """The 3D mask must be applied to every volume of a 4D image.

    Two geometries, because the failure differs. When the first axis and the
    volume count differ, the mask cannot broadcast and defacing raises. When
    they match, it broadcasts and writes wrong values instead.
    """
    nvolumes = 3
    indata = np.arange(1, np.prod(shape3d) * nvolumes + 1, dtype=np.int16).reshape(
        (*shape3d, nvolumes)
    )
    infile = tmp_path / 'sub-01_bold.nii.gz'
    nib.Nifti1Image(indata, np.eye(4)).to_filename(infile)

    monkeypatch.setenv('FSLDIR', str(tmp_path))
    monkeypatch.setattr(pdu.shutil, 'which', lambda name: '/usr/bin/' + name)
    monkeypatch.setattr(pdu.fsl, 'FLIRT', _make_flirt_stub(shape3d))

    pdu.deface_image(infile=str(infile), forcecleanup=True)

    outdata = np.asarray(
        nib.load(tmp_path / 'sub-01_bold_defaced.nii.gz').dataobj
    ).astype(np.int16)

    # The mask zeroes a single voxel, which must be zeroed in every volume,
    # while every other voxel keeps its original value in every volume.
    expected = indata.copy()
    expected[0, 0, 0, :] = 0
    assert outdata.shape == indata.shape
    assert (outdata[0, 0, 0, :] == 0).all()
    assert (outdata[1, 1, 1, :] == indata[1, 1, 1, :]).all()
    assert np.array_equal(outdata, expected)
