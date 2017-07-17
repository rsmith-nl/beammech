# file: test_EI.py
# vim:fileencoding=utf-8:fdm=marker:ft=python
#
# Author: R.F. Smith <rsmith@xs4all.nl>
# Created: 2017-07-17 10:29:56 +0200
# Last modified: 2017-07-17 11:09:14 +0200

"""Tests for EI berekening."""

import beammech as bm


def test_simple():
    """The most simple case; a single rectangle."""
    B = 100
    H = 20
    E = 210000
    sections = ((B, H, 0, E),)
    EI, top, bot = bm.EI(sections, E)
    EIc = E*B*(H**3)/12
    assert 0.99 < EI/EIc < 1.01
    assert top == H/2
    assert bot == -H/2


def test_simple_sw():
    """Simple sandwich"""
    B = 100
    h = 18
    t = 1
    H = h + 2 * t
    E = 20000
    sections = ((B, t, 0, E), (B, t, h+t, E))
    EI, top, bot = bm.EI(sections, E)
    EIc = E*B*(H**3 - h**3)/12
    assert 0.99 < EI/EIc < 1.01
    assert top == H/2
    assert bot == -H/2


def test_sw2():
    """Sandwich with different E for top and bottom layer"""
    B1 = 100
    B2 = 200
    h = 18
    t = 1
    H = h + 2 * t
    E1 = 20000
    E2 = 10000
    sections = ((B1, t, 0, E1), (B2, t, h+t, E2))
    EI, top, bot = bm.EI(sections, E1)
    EIc = E1*B1*(H**3 - h**3)/12
    assert 0.99 < EI/EIc < 1.01
