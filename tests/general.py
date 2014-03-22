#!/usr/bin/env python
# vim:fileencoding=utf-8
#
# Author: R.F. Smith <rsmith@xs4all.nl>
# Created: 2014-03-20 22:39:57 +0100
# Modified: $Date$
#
# To the extent possible under law, R.F. Smith has waived all copyright and
# related or neighboring rights to general.py. This work is published
# from the Netherlands. See http://creativecommons.org/publicdomain/zero/1.0/

"""Test cases for beammech."""

from __future__ import division, print_function
import beammech as bm
import math

E = 0.5*240000  # Young's Modulus of the beam's material in [MPa]
L = 1000  # Length of the beam in [mm]
P = -500  # Force in [N]
B = 400
H = 30
h = 26
I = B*(H**3 - h**3)/12
G = 28
GA = G*B*h
props = ([I]*(L+1), [GA]*(L+1), [H/2]*(L+1), [-H/2]*(L+1))


def compare(d, i, f):
    """Compare the result from beammech with the result from a formula.

    :param d: description of the situation
    :param i: integration result from beammech
    :param f: result from formula
    """
    result = "\033[31mFAIL\033[0m"
    if math.fabs((i-f)/f) < 0.005:
        result = "\033[32mPASS\033[0m"
    s = "{}. beammech: {:.3f} mm, formula: {:.3f} mm. {}"
    print(s.format(d, i, f, result))


def lc1():
    """Clamped beam with point load at end"""
    F = bm.Load(P, L)
    D, R1, _ = bm.shearforce(L, F, supports=None)
    _, y, _, _ = bm.loadcase(D, E, props, supports=None, shear=False)
    compare(lc1.__doc__, y[L], P*L**3/(3*E*I))


def lc2():
    """Clamped beam with distributed load"""
    Q = bm.DistLoad(P, (0, L))
    D, R1, _ = bm.shearforce(L, Q, supports=None)
    _, y, _, _ = bm.loadcase(D, E, props, supports=None, shear=False)
    compare(lc2.__doc__, y[L], P*L**3/(8*E*I))


def lc3():
    """Ends supported beam with distributed load"""
    supports = (0, L)
    Q = bm.DistLoad(P, supports)
    D, R1, _ = bm.shearforce(L, Q, supports)
    _, y, _, _ = bm.loadcase(D, E, props, supports=supports, shear=False)
    compare(lc3.__doc__, y[int(L/2)], 5*P*L**3/(384*E*I))


def lc4():
    """Ends supported beam with central point load"""
    supports = (0, L)
    F = bm.Load(P, int(L/2))
    D, R1, _ = bm.shearforce(L, F, supports)
    _, y, _, _ = bm.loadcase(D, E, props, supports=supports, shear=False)
    compare(lc4.__doc__, y[int(L/2)], P*L**3/(48*E*I))


def lc5():
    """Ends supported beam with triangle load"""
    supports = (0, L)
    F = bm.TriangleLoad(P, supports)
    D, R1, _ = bm.shearforce(L, F, supports)
    _, y, _, _ = bm.loadcase(D, E, props, supports=supports, shear=False)
    compare(lc5.__doc__, y[int(0.519*L)], 0.01304*P*L**3/(E*I))


def lc6():
    """Ends supported beam with three equidistant point loads"""
    supports = (0, L)
    loads = [bm.Load(P, L/4), bm.Load(P, L/2), bm.Load(P, 3*L/4)]
    D, R1, _ = bm.shearforce(L, loads, supports)
    _, y, _, _ = bm.loadcase(D, E, props, supports=supports, shear=False)
    compare(lc6.__doc__, y[int(L/2)], 19*P*L**3/(384*E*I))


if __name__ == '__main__':
    lc1()
    lc2()
    lc3()
    lc4()
    lc5()
    lc6()
