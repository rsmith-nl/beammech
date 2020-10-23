# file: test_EI.py
# vim:fileencoding=utf-8:fdm=marker:ft=python
#
# Author: R.F. Smith <rsmith@xs4all.nl>
# Created: 2017-07-17 10:29:56 +0200
# Last modified: 2017-07-17 21:33:08 +0200
"""Tests for EI berekening."""

import beammech as bm


def test_simple():
    """The most simple case; a single rectangle."""
    B = 100
    H = 20
    E = 210000
    sections = ((B, H, 0, E),)
    EI, top, bot = bm.EI(sections, E)
    EIc = E * B * (H ** 3) / 12
    assert 0.99 < EI / EIc < 1.01
    assert top == H / 2
    assert bot == -H / 2


def test_offsets():
    """Offsets should not influence the result."""
    B = 100
    H = 20
    E = 210000
    sections = ((B, H, 0, E),)
    sections2 = ((B, H, 12.435, E),)
    EI, top, bot = bm.EI(sections, E)
    EI2, top2, bot2 = bm.EI(sections2, E)
    assert 0.99 < EI / EI2 < 1.01
    assert 0.99 < top / top2 < 1.01
    assert 0.99 < bot / bot2 < 1.01


def test_simple_sw():
    """Simple sandwich"""
    B = 100
    h = 18
    t = 1
    H = h + 2 * t
    E = 20000
    sections = ((B, t, 0, E), (B, t, h + t, E))
    EI, top, bot = bm.EI(sections, E)
    EIc = E * B * (H ** 3 - h ** 3) / 12
    assert 0.99 < EI / EIc < 1.01
    assert top == H / 2
    assert bot == -H / 2


def test_uneven_sw():
    """Sandwich with different top and bottom layer width."""
    B = 100
    t = 1
    H = 30
    E = 20000
    sections = ((2 * B, t, 0, E), (B, t, H - t, E))
    EI, top, bot = bm.EI(sections, E)
    assert 1.95 < abs(bot) / top < 1.96


def test_sw2():
    """Sandwich with different E for top and bottom layer"""
    B1 = 100
    B2 = 200
    h = 18
    t = 1
    H = h + 2 * t
    E1 = 20000
    E2 = 10000
    sections = ((B1, t, 0, E1), (B2, t, h + t, E2))
    EI, top, bot = bm.EI(sections, E1)
    EIc = E1 * B1 * (H ** 3 - h ** 3) / 12
    assert 0.99 < EI / EIc < 1.01
