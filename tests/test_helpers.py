# file: test_helpers.py
# vim:fileencoding=utf-8:fdm=marker:ft=python
#
# Author: R.F. Smith <rsmith@xs4all.nl>
# Created: 2017-07-17 21:39:14 +0200
# Last modified: 2017-07-17 21:51:57 +0200

"""Tests for beammech helper functions"""

import numpy as np
from beammech import interpolate, _force, _start_end


def test_interpolate():
    assert np.all(interpolate([(0, 0), (3, 3)]) ==
                  np.array([0.,  1.,  2.,  3.]))
    assert np.all(interpolate([(0, 0), (4, 3), (6, -1)]) ==
                  np.array([0., 0.75, 1.5, 2.25, 3., 1., -1.]))
    assert np.all(interpolate([(1, 1), (4, 4), (6, -3)]) ==
                  np.array([1., 2., 3., 4., 0.5, -3.]))


def test_force():
    assert _force(kg=1) == -9.81
    assert _force(force=100) == 100


def test_start_end():
    assert _start_end(pos=(100, 200)) == (100, 200)
    assert _start_end(start=75, end=320) == (75, 320)
