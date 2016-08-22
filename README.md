Defacing tool for nifti images.  

Requirements:
- FSL
- nibabel
- nipype

####To install:

* git clone https://github.com/jmtyszka/pydeface.git
* cd pydeface
* python setup.py install

####To use:

pydeface.py -i infile.nii.gz

####Features:
This is a fork of the original pydeface from Russ Poldrack's lab. The defacing is implemented here as a 3D equivalent to the 2D "pixelation" seen in TV news footage. Let's call it "voxelation" for convenience. The same face mask is used as in the original, but the face region is downsampled using cubic spline interpolation then resampled to the original resolution using nearest-neighbor resampling. This prevents deconvolution restoration of the original data but retains sufficient intensity structure not to cause problems for 3D linear registration algorithms (eg affine registration).
