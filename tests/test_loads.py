# file: test_loads.py
# vim:fileencoding=utf-8:ft=python
#
# Author: R.F. Smith <rsmith@xs4all.nl>
# Created: 2015-08-24 01:34:26 +0200
# Last modified: 2015-08-24 22:38:21 +0200

"""
Tests for Load classes and load cases.

Run this test only with nosetests-3.4 -v test_loads.py
Run all tests with: nosetests-3.4 -v test_*
"""

from nose.tools import assert_raises
import beammech as bm
import numpy as np


E = 0.5*240000  # Young's Modulus of the beam's material in [MPa]
L = 1000  # Length of the beam in [mm]
P = -500  # Force in [N]
B = 400
H = 30
h = 26
I = B*(H**3 - h**3)/12
G = 28
A = B*h


def test_load_goodargs():
    """beammech.Load with correct arguments"""
    A = bm.Load(kg=1, pos=200)
    assert A.size == -9.81
    assert A.pos == 200
    B = bm.Load(force=-20, pos=300)
    assert B.size == -20
    assert B.pos == 300
    C = bm.Load(kg='1', pos='200')
    assert A.size == -9.81
    assert A.pos == 200


def test_load_badargs():
    """beammech.Load with faulty arguments"""
    assert_raises(KeyError, bm.Load)  # All required arguments missing
    assert_raises(KeyError, bm.Load, kg=-20)  # Required “pos” argument missing
    # Required “force” or “kg” argument missing
    assert_raises(KeyError, bm.Load, pos=231)
    # Required “force” argument misspelt
    assert_raises(KeyError, bm.Load, forse=-200, pos=300)
    # Argument “pos” or “force” cannot be converted to float
    assert_raises(ValueError, bm.Load, force=-120, pos='end')
    assert_raises(ValueError, bm.Load, force='-q', pos=200)


def test_clamped_pointload():
    """Clamped beam with point load at end"""
    problem = {'length': L, 'EI': np.ones(L+1)*E*I, 'GA': np.ones(L+1)*G*A,
               'top': np.ones(L+1)*H/2, 'bot': -np.ones(L+1)*H/2,
               'shear': False, 'supports': None,
               'loads': bm.Load(force=P, pos=L)}
    bm.solve(problem)
    deflection_bm = problem['y'][L]
    deflection_formula = P*L**3/(3*E*I)
    reldiff = abs((deflection_bm-deflection_formula)/deflection_formula)
    assert reldiff < 0.005


def test_clamped_distributed():
    """Clamped beam with distributed load"""
    problem = {'length': L, 'EI': np.ones(L+1)*E*I, 'GA': np.ones(L+1)*G*A,
               'top': np.ones(L+1)*H/2, 'bot': -np.ones(L+1)*H/2,
               'shear': False, 'supports': None,
               'loads': bm.DistLoad(force=P, start=0, end=L)}
    bm.solve(problem)
    deflection_bm = problem['y'][L]
    deflection_formula = P*L**3/(8*E*I)
    reldiff = abs((deflection_bm-deflection_formula)/deflection_formula)
    assert reldiff < 0.005


def test_supported_central_pointload():
    """Ends supported beam with central point load"""
    problem = {'length': L, 'EI': np.ones(L+1)*E*I, 'GA': np.ones(L+1)*G*A,
               'top': np.ones(L+1)*H/2, 'bot': -np.ones(L+1)*H/2,
               'supports': (0, L), 'shear': False,
               'loads': bm.Load(force=P, pos=L/2)}
    bm.solve(problem)
    deflection_bm = problem['y'][L/2]
    deflection_formula = P*L**3/(48*E*I)
    reldiff = abs((deflection_bm-deflection_formula)/deflection_formula)
    assert reldiff < 0.005


def test_supported_distributed():
    """Ends supported beam with distributed load"""
    problem = {'length': L, 'EI': np.ones(L+1)*E*I, 'GA': np.ones(L+1)*G*A,
               'top': np.ones(L+1)*H/2, 'bot': -np.ones(L+1)*H/2,
               'supports': (0, L), 'shear': False,
               'loads': bm.DistLoad(force=P, start=0, end=L)}
    bm.solve(problem)
    deflection_bm = problem['y'][L/2]
    deflection_formula = 5*P*L**3/(384*E*I)
    reldiff = abs((deflection_bm-deflection_formula)/deflection_formula)
    assert reldiff < 0.005


def test_supported_distributed():
    """Ends supported beam with triangle load"""
    problem = {'length': L, 'EI': np.ones(L+1)*E*I, 'GA': np.ones(L+1)*G*A,
               'top': np.ones(L+1)*H/2, 'bot': -np.ones(L+1)*H/2,
               'supports': (0, L), 'shear': False,
               'loads': bm.TriangleLoad(force=P, start=0, end=L)}
    bm.solve(problem)
    deflection_bm = problem['y'][int(0.519*L)]
    deflection_formula = 0.01304*P*L**3/(E*I)
    reldiff = abs((deflection_bm-deflection_formula)/deflection_formula)
    assert reldiff < 0.005


def test_supported_distributed():
    """Ends supported beam with three equidistant point loads"""
    problem = {'length': L, 'EI': np.ones(L+1)*E*I, 'GA': np.ones(L+1)*G*A,
               'top': np.ones(L+1)*H/2, 'bot': -np.ones(L+1)*H/2,
               'supports': (0, L), 'shear': False,
               'loads': [bm.Load(force=P, pos=L/4),
                         bm.Load(force=P, pos=L/2),
                         bm.Load(force=P, pos=3*L/4)]}
    bm.solve(problem)
    deflection_bm = problem['y'][L/2]
    deflection_formula = 19*P*L**3/(384*E*I)
    reldiff = abs((deflection_bm-deflection_formula)/deflection_formula)
    assert reldiff < 0.005


def test_gvepet1():
    """3-point bending GVEPET1 panel"""
    L = 200  # mm
    B = 50  # mm
    h = 28  # mm
    t = 1.3  # mm
    E = 22185  # MPa
    G = 8*1.5  # MPa, schuim met siktsels
    P = -150  # N
    H = h + 2*t
    I = B*(H**3-h**3)/12
    A = B*h
    problem = {'length': L, 'EI': np.ones(L+1)*E*I, 'GA': np.ones(L+1)*G*A,
               'top': np.ones(L+1)*H/2, 'bot': -np.ones(L+1)*H/2,
               'supports': (0, L), 'shear': False,
               'loads': bm.Load(force=P, pos=L/2)}
    bm.solve(problem)
    bending_bm = problem['y'][L/2]
    bending_formula = P*L**3/(48*E*I)
    problem["shear"] = True
    bm.solve(problem)
    total_bm = problem['y'][L/2]
    total_formula = bending_formula + (1.5*P/2*L/2)/(G*A)
    reldiff = abs((bending_bm-bending_formula)/bending_formula)
    assert reldiff < 0.005
    reldifft = abs((total_bm - total_formula)/total_formula)
    assert reldifft < 0.02


def test_cvepet3():
    """3-point bending CVEPET3 panel"""
    L = 200  # mm
    B = 50  # mm
    h = 26  # mm
    t = 2.5  # mm
    E = 43820  # MPa
    G = 8*1.5  # MPa, schuim met siktsels
    P = -150  # N
    H = h + 2*t
    I = B*(H**3-h**3)/12
    A = B*h
    problem = {'length': L, 'EI': np.ones(L+1)*E*I, 'GA': np.ones(L+1)*G*A,
               'top': np.ones(L+1)*H/2, 'bot': -np.ones(L+1)*H/2,
               'supports': (0, L), 'shear': False,
               'loads': bm.Load(force=P, pos=L/2)}
    bm.solve(problem)
    bending_bm = problem['y'][L/2]
    bending_formula = P*L**3/(48*E*I)
    problem["shear"] = True
    bm.solve(problem)
    total_bm = problem['y'][L/2]
    total_formula = bending_formula + (1.5*P/2*L/2)/(G*A)
    reldiff = abs((bending_bm-bending_formula)/bending_formula)
    assert reldiff < 0.005
    reldifft = abs((total_bm - total_formula)/total_formula)
    assert reldifft < 0.02
