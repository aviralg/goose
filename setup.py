# -*- coding: utf-8 -*-

"""
The following resources have been really helpful in making this setup script -

https://github.com/numpy/numpy/blob/master/setup.py
https://packaging.python.org/en/latest/index.html
https://github.com/pypa/sampleproject/blob/master/setup.py
https://docs.python.org/2/distutils/apiref.html
http://stackoverflow.com/questions/3207219/how-to-list-all-files-of-a-directory-in-python
"""

from setuptools import setup, Extension
import sys
import os

here = os.path.dirname(__file__)

with open(os.path.join(here, 'requirements.txt')) as f:
    requires = f.read().splitlines()

long_description = open(os.path.join(here,"README.rst")).read()

scripts_dir = os.path.join(here, "src/scripts")
scripts = [os.path.join(scripts_dir,fn) for fn in next(os.walk(scripts_dir))[2]]

setup( name             =   'goose'
     , author           =   ",".join(["Aviral Goel", "HarshaRani"])
     , author_email     =   ",".join(["aviralg@ncbs.res.in", "hrani@ncbs.res.in"])
     , maintainer       =   ",".join(["Aviral Goel", "HarshaRani"])
     , maintainer_email =   ",".join(["aviralg@ncbs.res.in", "hrani@ncbs.res.in"])
     , version          =   "0.0.0"
     , url              =   ''
     , download_url     =   ''
     , description      =   "GOOSE - Graphical user interface for mOOSE"
     , long_description =   long_description
     , classifiers      =   [ 'Development Status :: 3 - Alpha'
                            , 'Environment :: X11 Applications :: Qt'
                            , 'Intended Audience :: Science/Research'
                            , "License :: OSI Approved :: GNU General Public License v2 (GPLv2)"
                            , 'Programming Language :: Python :: 2.6'
                            , 'Programming Language :: Python :: 2.7'
                            , 'Programming Language :: C++'
                            , 'Natural Language :: English'
                            , 'Operating System :: OS Independent'
                            , 'Topic :: Scientific/Engineering'
                            ]
     , license          =   'GPLv2'
     , install_requires         =   requires
     , packages         =   [ "goose"
                            , "goose.utils"
                            , "goose.widgets"
                            ]
     , package_dir      =   { ''    :   "src"
                            }
     , package_data     =   { ''    :   [ 'src/goose/data/*/*'
                                        ]
                            }
     , scripts          =   scripts
)
