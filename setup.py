# file: setup.py
# vim:fileencoding=utf-8:ft=python
# Installation script for beammech
#
# Author: R.F. Smith <rsmith@xs4all.nl>
# Created: 2015-04-28 19:45:39 +0200
# Last modified: 2015-09-20 16:57:35 +0200

from distutils.core import setup

with open('README.rst') as file:
    ld = file.read()


setup(name='beammech',
      version='0.10.1',
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
      long_description=ld
      )
