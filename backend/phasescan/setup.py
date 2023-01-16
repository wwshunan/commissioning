from distutils.core import setup
from Cython.Build import cythonize
import numpy 

setup(name="cfit", ext_modules=cythonize("cfit.pyx"), include_dirs=[numpy.get_include()])