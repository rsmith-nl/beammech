#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2012-2014 R.F. Smith <rsmith@xs4all.nl>. All rights reserved.
# $Date$
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY AUTHOR AND CONTRIBUTORS “AS IS” AND ANY EXPRESS
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN
# NO EVENT SHALL AUTHOR OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Module for stiffness and strength calculations of beams."""

from __future__ import division, print_function
import numpy as np
import math

__version__ = '$Revision$'[11:-2]


class Load(object):
    """Point load."""

    def __init__(self, size, pos):
        """Create a point load.

        :param size: force in Newtons.
        :param pos: distance of the force from the origin in mm.
        """
        self.size = float(size)
        self.pos = int(pos)

    def __str__(self):
        return "point load of {} N @ {} mm.".format(self.size, self.pos)

    def moment(self, pos):
        """Returns the bending moment the load exerts at pos.
        """
        return (self.pos-pos)*self.size

    def shear(self, length):
        """Return the contribution of the load to the shear.

        :param length: length of the array to return
        :returns: array that contains the contribution of this load.
        """
        rv = np.zeros(length+1)
        rv[self.pos:] = self.size
        return rv


class DistLoad(Load):
    """Evenly distributed load."""

    def __init__(self, size, pos):
        """Create an evenly distributed load.

        :param size: force in Newtons.
        :param pos: 2-tuple containing the borders of the distributed load.
        """
        self.start = int(min(pos))
        self.end = int(max(pos))
        Load.__init__(self, size, float(self.start+self.end)/2)

    def __str__(self):
        r = "constant distributed load of {} N @ {}--{} mm."
        return r.format(self.size, self.start, self.end)

    def shear(self, length):
        rem = length + 1 - self.end
        d = self.end-self.start
        q = self.size
        parts = (np.zeros(self.start), np.linspace(0, q, d),
                 np.ones(rem)*q)
        return np.concatenate(parts)


class TriangleLoad(DistLoad):
    """Linearly rising distributed load."""

    def __init__(self, size, pos):
        DistLoad.__init__(self, size, pos)
        length = max(pos)-min(pos)
        self.pos = min(pos)+2.0*length/3.0
        self.q = 2*self.size/length

    def __str__(self):
        r = "linearly {} distributed load of {} N @ {}--{} mm."
        if self.start < self.end:
            direction = 'ascending'
        else:
            direction = 'descending'
        return r.format(direction, self.size, self.start, self.end)

    def shear(self, length):
        rem = length + 1 - self.end
        parts = (np.zeros(self.start),
                 np.linspace(0, self.q, self.end-self.start),
                 np.ones(rem)*self.q)
        dv = np.concatenate(parts)
        return np.cumsum(dv)


def patientload(mass, s):
    """Returns a list of DistLoads that represent a patient
    load according to IEC 60601 specs.

    :param mass: mass of the patient in kg.
    :param s: location of the feet in mm, head lies at s+1900
    :returns: a list of Loads
    """
    f = -kg2N(mass)
    fractions = [(0.148*f, (s + 0, s + 450)),  # l. legs, 14.7% from 0--450 mm
                 (0.222*f, (s + 450, s + 1000)),  # upper legs
                 (0.074*f, (s + 1000, s + 1180)),  # hands
                 (0.408*f, (s + 1000, s + 1700)),  # torso
                 (0.074*f, (s + 1200, s + 1700)),  # arms
                 (0.074*f, (s + 1220, s + 1900))]  # head
    return [DistLoad(i[0], i[1]) for i in fractions]


def shearforce(length, loads, supports=None):
    """Calculates a list of shear force element based on a list of loads. The
    returned list has a resolution of 1 mm per element. The shear
    force element at index p goes from from nodes p to p+1.

    :param length: length of the product in millimeters.
    :param loads: list of Loads.
    :param supports: a 2-tuple of the location in mm of the supports, or
    None if the beam is clamped at x=0.
    :returns: a 3-tuple consisting of a list of shear values, reaction
    Load R1 and either Load R2 for a simple support or reaction moment
    R1 when clamped.
    """
    length = int(length)
    if length < 1:
        raise ValueError('Beam of negative length is impossible.')
    if isinstance(loads, list):
        if len(loads) == 0:
            raise ValueError('No loads specified')
        for ld in loads:
            assert ld.pos >= 0 and ld.pos <= length, 'Load outside length'
    elif isinstance(loads, Load):
        loads = [loads]
    else:
        raise ValueError("'loads' is not a Load or a list of Loads")
    s1, s2 = _supcheck(length, supports)
    # Moment balance around s1
    moment = sum([ld.moment(s1) for ld in loads])
    if s2:
        R2 = Load(-moment/(s2-s1), s2)
        loads.append(R2)
    else:  # clamped at x = 0
        R2 = -moment
    # Force equilibrium
    R1 = Load(-sum([ld.size for ld in loads]), s1)
    loads.append(R1)
    V = np.sum(np.array([ld.shear(length) for ld in loads]), axis=0)
    return V, R1, R2


def loadcase(D, E, props, supports=None, shear=True, strain=False):
    """Calculates a loadcase.

    :param D: List of shear force values along the length of the beam.
    :param E: Young's Modulus of the homogenized beam.
    :param props: a four-tuple of arrays (I, GA, etop, ebot). The I is the
    second area moment of the homogenized cross-section in mm⁴. GA is the
    shear stiffness in N. The e* values are the distance from the neutral line
    of the cross-section to the top and bottom of the material in mm
    respectively. The latter should be negative.
    :param supports: A list of positions of the two supports, or None of
    the beam is clamped at x=0.
    :param shear: Indicates wether shear deflection should be taken into
    account. True by default.
    :param strain: Indicates wether strains should be reported at the top and
    bottom surfaces. False by default.
    :returns: a tuple of four lists containing the bending moment,
    deflection, stress (or strain) at the top and the bottom of the
    cross-section.
    """
    s1, s2 = _supcheck(len(D), supports)
    M = np.cumsum(D)
    if s2 is None:
        M -= M[-1]
    I, GA, etop, ebot = props
    I, GA = np.array(I), np.array(GA)
    etop, ebot = np.array(etop), np.array(ebot)
    top = -M*etop/I
    bottom = -M*ebot/I
    if strain:
        top /= E
        bottom /= E
    ddy_b = M/(E*I)
    dy_b = np.cumsum(ddy_b)
    if shear:
        dy_sh = -1.5*D/GA
        dy_tot = dy_b + dy_sh
    else:
        dy_tot = dy_b
    y_tot = np.cumsum(dy_tot)
    y_tot = align(y_tot, s1, s2)
    return (M, y_tot, top, bottom)


def calculate(length, loads, E, props, supports=None, shear=True):
    """Convenience function to combine the whole calculation.

    :length: The length of the beam in mm.
             The leftmost end of the beam is x=0.
    :loads: Either an instance of a Load, or a list or tuple of them.
    :E: The homogenized Young's modulus of the beam's material.
    :xsecprops: A function that defines the properties of the cross-section.
    :supports: A list or tuple of the two locations (in mm) where the beam is
               supported, or None. In the latter case the beam is clamped
               at x=0
    :shear: A boolean that indicates whether the contribution of shear to the
    deflection is to be taken into account.
    """
    D, R1, R2 = shearforce(length, loads, supports)
    M, y, st, sb = loadcase(D, E, props, supports, shear)
    return D, M, y, st, sb, R1, R2


def kg2N(k):
    """Converts kilograms to Newtons.

    :param k: string or number in kilograms
    :returns: a float containing the equivalent of k in N.
    """
    return float(k)*9.81


def align(src, s1, s2):
    """In the situation with two supports, transform a list of values such
    that the value at the supports is zero.

    :param src: a numpy array of values
    :param s1: location where the first support is
    :param s2: location of the second support or None
    :returns: a transformed src whose values at indiced s1 and s2 is 0
    """
    if s2 is None:
        return src
    # First, translate the whole list so that the value at the
    # index anchor is zero.
    translated = src - src[s1]
    # Then rotate around the anchor so that the deflection at the other
    # support is also 0.
    delta = -translated[s2]/math.fabs(s1-s2)
    slope = np.concatenate((np.arange(-s1, 1, 1),
                            np.arange(1, len(src)-s1)))*delta
    rv = translated + slope
    return rv


def _supcheck(length, spts):
    """Check the supports argument.

    :param length: length of the beam
    :param spts: a 2-tuple of support positions or None
    :returns: a valid 2-tuple of supports
    """
    if spts is None:
        return (0, None)
    if len(spts) != 2:
        raise ValueError('There must be two supports!')
    if isinstance(spts[0], Load):
        t = [spts[0].pos, spts[1].pos]
    else:
        t = [int(spts[0]), int(spts[1])]
    rv = (min(t), max(t))
    if rv[0] < 0 or rv[1] > length:
        raise ValueError('Support(s) outside the length of the beam.')
    return rv
