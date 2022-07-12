[![DOI](https://zenodo.org/badge/47563497.svg)](https://zenodo.org/badge/latestdoi/47563497)

<img src="/visuals/logo.svg" width=250 align="right" />

# PyDeface
A tool to remove facial structure from MRI images.

## Dependencies:
| Package                                          | Tested version |
|--------------------------------------------------|----------------|
| [FSL](https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FSL)| 6.0.3          |
| [Python 3](https://www.python.org/downloads/)    | 3.7.3          |
| [NumPy](http://www.numpy.org/)                   | 1.21.6         |
| [NiBabel](http://nipy.org/nibabel/)              | 4.0.1          |
| [Nipype](http://nipype.readthedocs.io/en/latest/)| 1.5.1          |

## Installation
```
pip install pydeface
```
or
```
git clone https://github.com/poldracklab/pydeface.git
cd pydeface
python setup.py install
```

## How to use
```
pydeface infile.nii.gz
```

Also see the help for additional options:
```
pydeface --help
```

## License
PyDeface is licensed under [MIT license](LICENSE.txt).
