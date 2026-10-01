import os
import tempfile
from pathlib import Path
from shutil import which

import pytest

import pydeface.utils as pdu


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


def test_generate_tmpfiles_closes_descriptors():
    fd_dir = Path('/proc/self/fd')
    if not fd_dir.exists():
        pytest.skip('needs /proc/self/fd')
    before = len(os.listdir(fd_dir))
    for _ in range(5):
        pdu.cleanup_files(*pdu.generate_tmpfiles(verbose=False))
    assert len(os.listdir(fd_dir)) == before


def test_deface_image_leaves_no_matrix_file(monkeypatch, tmp_path):
    import nibabel as nib
    import numpy as np
    from nipype.interfaces import fsl

    def fake_run(self):
        img = nib.Nifti1Image(np.ones((4, 4, 4), dtype='f4'), np.eye(4))
        nib.save(img, self.inputs.out_file)

    infile = tmp_path / 'in.nii.gz'
    nib.save(nib.Nifti1Image(np.ones((4, 4, 4), dtype='f4'), np.eye(4)), infile)
    tmp_dir = tmp_path / 'tmp'
    tmp_dir.mkdir()
    monkeypatch.setattr('tempfile.tempdir', str(tmp_dir))
    monkeypatch.setattr(pdu.shutil, 'which', lambda name: '/fsl/bin/flirt')
    monkeypatch.setenv('FSLDIR', '/fsl')
    monkeypatch.setattr(fsl.FLIRT, 'run', fake_run)

    pdu.deface_image(str(infile), force=True, forcecleanup=True, verbose=False)

    assert list(tmp_dir.iterdir()) == []


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
