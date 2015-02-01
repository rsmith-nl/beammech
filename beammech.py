# file: beammech.py
# vim:fileencoding=utf-8:ft=python
# Copyright © 2012-2015 R.F. Smith <rsmith@xs4all.nl>. All rights reserved.
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

    def __init__(self, **kwargs):
        """Create a point load.

        :param force: force in Newtons.
        :param kg: weight of a mass in kg, alternative for force.
        :param pos: distance of the force from the origin in mm.
        """
        self.size = _force(kwargs)
        self.pos = round(float(kwargs['pos']))

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

    def __init__(self, **kwargs):
        """Create an evenly distributed load.

        :param force: force in Newtons.
        :param kg: weight of a mass in kg, alternative for force.
        :param start: begin of the distributed load
        :param start: end of the distributed load
        :param pos: 2-tuple containing the borders of the distributed load.
        You can use this instead of start and end.
        """
        size = _force(kwargs)
        self.start, self.end = _start_end(kwargs)
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


# class TriangleLoad(DistLoad):
#    """Linearly rising distributed load."""
#
#    def __init__(self, **kwargs):
#        DistLoad.__init__(self, kwargs)
#        length = abs(self.start - self.end)
#        self.pos = int(round(min(pos))) + 2.0*length/3.0
#        self.q = 2*self.size/length
#
#    def __str__(self):
#        r = "linearly {} distributed load of {} N @ {}--{} mm."
#        if self.start < self.end:
#            direction = 'ascending'
#        else:
#            direction = 'descending'
#        return r.format(direction, self.size, self.start, self.end)
#
#    def shear(self, length):
#        rem = length + 1 - self.end
#        parts = (np.zeros(self.start),
#                 np.linspace(0, self.q, self.end-self.start),
#                 np.ones(rem)*self.q)
#        dv = np.concatenate(parts)
#        return np.cumsum(dv)


def _force(kwargs):
    """Get the force out of kwargs.

    :param kwargs: keyword arguments. Allowed keys 'force' or 'kg'.
    :returns: force as a float
    """
    if 'force' in kwargs:
        force = float(kwargs['force'])
    elif 'kg' in kwargs:
        force = -9.81*float(kwargs['kg'])
    else:
        raise KeyError("No 'force' or 'kg' present")
    return force


def _start_end(kwargs):
    """Get the (start, end) out of kwargs.

    :param kwargs: keyword arguments. Required keys 'start' and 'end' or 'pos'.
    :returns: postition as a (start, end) tuple
    """
    if 'pos' in kwargs:
        p = kwargs['pos']
        if not isinstance(p, tuple) and len(p) != 2:
            raise ValueError("'pos' should be a 2-tuple")
        pos = (round(float(pos[0])), round(float(pos[1])))
    elif 'start' in kwargs and 'end' in kwargs:
        pos = (round(float(kwargs['start'])), round(float(kwargs['end'])))
    else:
        raise KeyError("Neither 'pos' or 'start' and 'end' present")
    return pos


def _check_length_supports(problem):
    """Validate if the problem contains proper length and supports

    :param problem: dictionary containing the parameters of the problem
    :returns: length, supports. This function raises exceptions when
    problems are found.
    """
    problem['length'] = int(round(problem['length']))
    if problem['length'] < 1:
        raise ValueError('length must be ≥1')
    if 'supports' in problem:
        s = problem['supports']
        if len(s) != 2:
            t = 'The problem definition must contain exactly two supports.'
            raise ValueError(t)
        s = (int(round(s[0])), int(round(s[1])))
        if s[0] == s[1]:
            raise ValueError('Two identical supports found!')
        elif s[0] > s[1]:
            s = (s[1], s[0])
        if s[0] < 0 or s[1] > problem['length']:
            raise ValueError('Support(s) outside of the beam!')
        problem['supports'] = s
    else:
        s = (0, None)
    return (length, s)


def _check_loads(problem):
    """Validate the loads in the problem

    :param problem: dictionary containing the parameters of the problem
    :returns: tuple of loads. This function raises exceptions when
    problems are found.
    """
    loads = problem['loads']
    if isinstance(loads, Load):
        loads = [loads]
        problem['loads'] = loads
    if loads is None or len(loads) == 0:
        raise ValueError('No loads specified')
    for ld in loads:
        if not isinstance(ld, Load):
            raise ValueError('Loads must be Load instances')
    return list(loads)


def _check_arrays(problem):
    """Validate the length of the EI, GA, top and bot arrays.

    :param problem: @todo
    :returns: @todo
    """
    L = problem['length']
    t = "Length of array {} ({}) doesn't match beam length ({}) + 1 ."
    for key in ['EI', 'GA', 'top', 'bot']:
        if not isinstance(problem[key], np.ndarray):
            problem[key] = np.array(problem[key])
        la = len(problem[key])
        if la != L + 1:
            raise ValueError(t.format(key, la, L))
    return problem['EI'], problem['GA'], problem['top'], problem['bot']


def patientload(**kwargs):
    """Returns a list of DistLoads that represent a patient
    load according to IEC 60601 specs.

    :param kg: The mass of the patient in kg.
    :param force: The force in N. Alternative for kg
    :param feet: Location of the feet in mm
    :param head: Location of the head in mm. Alternative for 'feet'.
    :returns: A list of Loads.
    """
    f = _force(kwargs)
    if 'feet' in kwargs:
        s = round(float(kwargs['feet']))
    elif 'head' in kwargs:
        s = round(float(kwargs['head'])) - 1900
    fractions = [(0.148*f, (s + 0, s + 450)),  # l. legs, 14.7% from 0--450 mm
                 (0.222*f, (s + 450, s + 1000)),  # upper legs
                 (0.074*f, (s + 1000, s + 1180)),  # hands
                 (0.408*f, (s + 1000, s + 1700)),  # torso
                 (0.074*f, (s + 1200, s + 1700)),  # arms
                 (0.074*f, (s + 1220, s + 1900))]  # head
    return [DistLoad(force=i[0], pos=i[1]) for i in fractions]


def solve(problem):
    """Solve the beam problem.

    :param problem: dictionary containing the parameters of the problem
    :returns: No value is returned. The ‘problem’ parameter dictionary is
    updated with the results.
    """
    length, (s1, s2) = _check_length_supports(problem)
    loads = _check_loads(problem)
    EI, GA, top, bot = _check_arrays(problem)
    moment = sum([ld.moment(s1) for ld in loads])
    if s2:
        R2 = Load(-moment/(s2-s1), s2)
        loads.append(R2)
    else:  # clamped at x = 0
        R2 = -moment
    # Force equilibrium
    R1 = Load(-sum([ld.size for ld in loads]), s1)
    loads.append(R1)
    D = np.sum(np.array([ld.shear(length) for ld in loads]), axis=0)
    M = np.cumsum(D)
    if s2 is None:
        M -= M[-1]
    ddy_b = M/EI
    etop, ebot = -top*ddy_b, -bot*ddy_b
    dy = np.cumsum(ddy_b)
    dy += -1.5*D/GA  # shear
    y = np.cumsum(dy)
    if s2:
        # First, translate the whole list so that the value at the
        # index anchor is zero.
        translated = y - y[s1]
        # Then rotate around the anchor so that the deflection at the other
        # support is also 0.
        delta = -y[s2]/math.fabs(s1-s2)
        slope = np.concatenate((np.arange(-s1, 1, 1),
                                np.arange(1, len(y)-s1)))*delta
        dy += delta
        y = translated + slope
    problem['D'], problem['M'] = M
    problem['y'], problem['R'] = y, (R1, R2)
    problem['a'] = np.rad2deg(np.arctan(dy))
