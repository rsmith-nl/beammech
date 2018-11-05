# file: test_loads.py
# vim:fileencoding=utf-8:ft=python:fdm=marker
#
# Author: R.F. Smith <rsmith@xs4all.nl>
# Created: 2015-08-24 01:34:26 +0200
# Last modified: 2018-11-05T21:46:25+0100
"""
Tests for Load classes and load cases.
"""
import pytest
import beammech as bm
import numpy as np

E = 0.5 * 240000  # Young's Modulus of the beam's material in [MPa]
L = 1000  # Length of the beam in [mm]
P = -500  # Force in [N]
B = 400
H = 30
h = 26
Ix = B * (H**3 - h**3) / 12
G = 28
A = B * h


def test_load_goodargs():  # {{{1
    """beammech.Load with correct arguments"""
    A = bm.Load(kg=1, pos=200)
    assert A.size == -9.81
    assert A.pos == 200
    B = bm.Load(force=-20, pos=300)
    assert B.size == -20
    assert B.pos == 300
    C = bm.Load(kg='1', pos='200')
    assert C.size == -9.81
    assert C.pos == 200


def test_load_badargs():  # {{{1
    """beammech.Load with faulty arguments"""
    with pytest.raises(KeyError):
        bm.Load()  # All required arguments missing
    with pytest.raises(KeyError):
        bm.Load(kg=-20)  # Required “pos” argument missing
    # Required “force” or “kg” argument missing
    with pytest.raises(KeyError):
        bm.Load(pos=231)
    # Required “force” argument misspelt
    with pytest.raises(KeyError):
        bm.Load(forse=-200, pos=300)
    # Argument “pos” or “force” cannot be converted to float
    with pytest.raises(ValueError):
        bm.Load(force=-120, pos='end')
    with pytest.raises(ValueError):
        bm.Load(force='-q', pos=200)


def test_clamped_pointload():  # {{{1
    """Clamped beam with point load at end"""
    results = bm.solve(
        L, None, bm.Load(force=P, pos=L),
        np.ones(L + 1) * E * Ix,
        np.ones(L + 1) * G * A,
        np.ones(L + 1) * H / 2, -np.ones(L + 1) * H / 2, False
    )
    deflection_bm = results['y'][L]
    deflection_formula = P * L**3 / (3 * E * Ix)
    reldiff = abs((deflection_bm - deflection_formula) / deflection_formula)
    assert reldiff < 0.005


def test_clamped_distributed():  # {{{1
    """Clamped beam with distributed load"""
    results = bm.solve(
        L, None, bm.DistLoad(force=P, start=0, end=L),
        np.ones(L + 1) * E * Ix,
        np.ones(L + 1) * G * A,
        np.ones(L + 1) * H / 2, -np.ones(L + 1) * H / 2, False
    )
    deflection_bm = results['y'][L]
    deflection_formula = P * L**3 / (8 * E * Ix)
    reldiff = abs((deflection_bm - deflection_formula) / deflection_formula)
    assert reldiff < 0.005


def test_supported_central_pointload():  # {{{1
    """Ends supported beam with central point load"""
    results = bm.solve(
        L, (0, L), bm.Load(force=P, pos=L / 2),
        np.ones(L + 1) * E * Ix,
        np.ones(L + 1) * G * A,
        np.ones(L + 1) * H / 2, -np.ones(L + 1) * H / 2, False
    )
    deflection_bm = results['y'][int(L / 2)]
    deflection_formula = P * L**3 / (48 * E * Ix)
    reldiff = abs((deflection_bm - deflection_formula) / deflection_formula)
    assert reldiff < 0.005


def test_supported_distributed():  # {{{1
    """Ends supported beam with distributed load"""
    results = bm.solve(
        L, (0, L), bm.DistLoad(force=P, start=0, end=L),
        np.ones(L + 1) * E * Ix,
        np.ones(L + 1) * G * A,
        np.ones(L + 1) * H / 2, -np.ones(L + 1) * H / 2, False
    )
    deflection_bm = results['y'][int(L / 2)]
    deflection_formula = 5 * P * L**3 / (384 * E * Ix)
    reldiff = abs((deflection_bm - deflection_formula) / deflection_formula)
    assert reldiff < 0.005


def test_supported_triangl():  # {{{1
    """Ends supported beam with triangle load"""
    results = bm.solve(
        L, (0, L), bm.TriangleLoad(force=P, start=0, end=L),
        np.ones(L + 1) * E * Ix,
        np.ones(L + 1) * G * A,
        np.ones(L + 1) * H / 2, -np.ones(L + 1) * H / 2, False
    )
    deflection_bm = results['y'][int(0.519 * L)]
    deflection_formula = 0.01304 * P * L**3 / (E * Ix)
    reldiff = abs((deflection_bm - deflection_formula) / deflection_formula)
    assert reldiff < 0.005


def test_supported_pointloads():  # {{{1
    """Ends supported beam with three equidistant point loads"""
    results = bm.solve(
        L, (0, L), [
            bm.Load(force=P, pos=L / 4),
            bm.Load(force=P, pos=L / 2),
            bm.Load(force=P, pos=3 * L / 4)
        ],
        np.ones(L + 1) * E * Ix,
        np.ones(L + 1) * G * A,
        np.ones(L + 1) * H / 2, -np.ones(L + 1) * H / 2, False
    )
    deflection_bm = results['y'][int(L / 2)]
    deflection_formula = 19 * P * L**3 / (384 * E * Ix)
    reldiff = abs((deflection_bm - deflection_formula) / deflection_formula)
    assert reldiff < 0.005


def test_supported_moment_end():
    """Ends supported beam with moment load at end."""
    M = 500 * 1000
    x = L - 422
    results = bm.solve(
        L, (0, L), bm.MomentLoad(-M, L),
        np.ones(L + 1) * E * Ix,
        np.ones(L + 1) * G * A,
        np.ones(L + 1) * H / 2, -np.ones(L + 1) * H / 2, False
    )
    deflection_bm = results['y'][x]
    deflection_formula = 0.0642 * M * L**2 / (E * Ix)
    reldiff = abs((deflection_bm - deflection_formula) / deflection_formula)
    assert reldiff < 0.005


def test_supported_moment_both():
    """Ends supported beam with moment load at both ends."""
    M = 500 * 1000 / 2
    results = bm.solve(
        L, (0, L), [bm.MomentLoad(M, 0), bm.MomentLoad(-M, L)],
        np.ones(L + 1) * E * Ix,
        np.ones(L + 1) * G * A,
        np.ones(L + 1) * H / 2, -np.ones(L + 1) * H / 2, False
    )
    deflection_bm = results['y'][int(L / 2)]
    deflection_formula = 6 * M * L**2 / (48 * E * Ix)
    reldiff = abs((deflection_bm - deflection_formula) / deflection_formula)
    assert reldiff < 0.005


def test_supported_moment_begin():
    """Ends supported beam with moment load at begin."""
    M = 500 * 1000
    x = 422
    results = bm.solve(
        L, (0, L), bm.MomentLoad(M, 0),
        np.ones(L + 1) * E * Ix,
        np.ones(L + 1) * G * A,
        np.ones(L + 1) * H / 2, -np.ones(L + 1) * H / 2, False
    )
    deflection_bm = results['y'][x]
    deflection_formula = 0.0642 * M * L**2 / (E * Ix)
    reldiff = abs((deflection_bm - deflection_formula) / deflection_formula)
    assert reldiff < 0.005


def test_clamped_moment_end():
    """Begin clamped, moment load at end."""
    M = 500 * 1000
    results = bm.solve(
        L, None, bm.MomentLoad(M, pos=L),
        np.ones(L + 1) * E * Ix,
        np.ones(L + 1) * G * A,
        np.ones(L + 1) * H / 2, -np.ones(L + 1) * H / 2, False
    )
    deflection_bm = results['y'][L]
    deflection_formula = M * L**2 / (2 * E * Ix)
    reldiff = abs((deflection_bm - deflection_formula) / deflection_formula)
    assert reldiff < 0.005


def test_gvepet1():  # {{{1
    """3-point bending GVEPET1 panel"""
    L = 200  # mm
    B = 50  # mm
    h = 28  # mm
    t = 1.3  # mm
    E = 22185  # MPa
    G = 8 * 1.5  # MPa, schuim met siktsels
    P = -150  # N
    H = h + 2 * t
    Ix = B * (H**3 - h**3) / 12
    A = B * h
    results = bm.solve(
        L, (0, L), bm.Load(force=P, pos=L / 2),
        np.ones(L + 1) * E * Ix,
        np.ones(L + 1) * G * A,
        np.ones(L + 1) * H / 2, -np.ones(L + 1) * H / 2, False
    )
    bending_bm = results['y'][int(L / 2)]
    bending_formula = P * L**3 / (48 * E * Ix)
    results = bm.solve(
        L, (0, L), bm.Load(force=P, pos=L / 2),
        np.ones(L + 1) * E * Ix,
        np.ones(L + 1) * G * A,
        np.ones(L + 1) * H / 2, -np.ones(L + 1) * H / 2, True
    )
    total_bm = results['y'][int(L / 2)]
    total_formula = bending_formula + (1.5 * P / 2 * L / 2) / (G * A)
    reldiff = abs((bending_bm - bending_formula) / bending_formula)
    assert reldiff < 0.005
    reldifft = abs((total_bm - total_formula) / total_formula)
    assert reldifft < 0.02


def test_cvepet3():  # {{{1
    """3-point bending CVEPET3 panel"""
    L = 200  # mm
    B = 50  # mm
    h = 26  # mm
    t = 2.5  # mm
    E = 43820  # MPa
    G = 8 * 1.5  # MPa, schuim met siktsels
    P = -150  # N
    H = h + 2 * t
    Ix = B * (H**3 - h**3) / 12
    A = B * h
    results = bm.solve(
        L, (0, L), bm.Load(force=P, pos=L / 2),
        np.ones(L + 1) * E * Ix,
        np.ones(L + 1) * G * A,
        np.ones(L + 1) * H / 2, -np.ones(L + 1) * H / 2, False
    )
    bending_bm = results['y'][int(L / 2)]
    bending_formula = P * L**3 / (48 * E * Ix)
    results = bm.solve(
        L, (0, L), bm.Load(force=P, pos=L / 2),
        np.ones(L + 1) * E * Ix,
        np.ones(L + 1) * G * A,
        np.ones(L + 1) * H / 2, -np.ones(L + 1) * H / 2, True
    )
    total_bm = results['y'][int(L / 2)]
    total_formula = bending_formula + (1.5 * P / 2 * L / 2) / (G * A)
    reldiff = abs((bending_bm - bending_formula) / bending_formula)
    assert reldiff < 0.005
    reldifft = abs((total_bm - total_formula) / total_formula)
    assert reldifft < 0.02
