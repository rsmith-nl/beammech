# -*- coding: utf-8 -*-
# Installation script for beammech
# R.F. Smith <rsmith@xs4all.nl>
# $Date$

from distutils.core import setup

with open('README.rst') as file:
    ld = file.read()


setup(name='beammech',
      version='$Revision$'[11:-2],
      license='BSD',
      description='Module to evaluate loaded beams.',
      author='Roland Smith', author_email='rsmith@xs4all.nl',
      url='http://rsmith.home.xs4all.nl/category/software.html',
      requires=['numpy'],
      py_modules=['beammech'],
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Environment :: Console',
                   'Intended Audience :: End Users/Desktop',
                   'Intended Audience :: Manufacturing',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3.4',
                   'Topic :: Scientific/Engineering'
                   ],
      long_description = ld
      )
