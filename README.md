# PyDeface
A defacing tool for MRI nifti images.

## Dependencies:

| Package                                          | Tested version |
|--------------------------------------------------|----------------|
| [Python 3](https://www.python.org/downloads/)    | 3.7.3          |
| [FSL](https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FSL)| 6.0.2          |
| [NiBabel](http://nipy.org/nibabel/)              | 2.5.1          |
| [Nipype](http://nipype.readthedocs.io/en/latest/)| 1.3.0-rc1      |

## To install:
```
git clone https://github.com/poldracklab/pydeface.git
cd pydeface
python setup.py install
```

## To use:
```
pydeface infile.nii.gz
```

Also see the help for additional options:
```
pydeface --help
```

## License
Nibabel is licensed under the [MIT license](/LICENSE).
