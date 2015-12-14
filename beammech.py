# file: beammech.py
# vim:fileencoding=utf-8:ft=python:fdm=indent
# Copyright © 2012-2015 R.F. Smith <rsmith@xs4all.nl>. All rights reserved.
# Last modified: 2015-12-15 00:08:19 +0100
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

import numpy as np
import math

__version__ = '0.10.1'


def solve(problem):
    """Solve the beam problem.

    Arguments:
        problem: A dictionary containing the parameters of the problem.
            For this function, the dictionary should have the following keys;
            * 'length': The length of the beam in mm. This will be rounded to
                an integer value.
            * 'supports': Either None or a 2-tuple of numbers between 0 and
                length. If None, the beam will be assumed to be clamped at the
                origin.
            * 'loads': Either a Load or an iterable of Loads.
            * 'EI': An iterable of size length+1 containing the bending
                stiffenss in every mm of the cross-section of the beam.
            * 'GA': An iterable of size length+1 containing the shear
                stiffenss in every mm of the cross-section of the beam.
            * 'top': An iterable of size length+1 containing the height
                above the neutral line in every mm of the cross-section of the
                beam.
            * 'bottom': An iterable of size length+1 containing the height
                under the neutral line in every mm of the cross-section of the
                beam.
            * 'shear': A boolean indication if shear deformations should be
                included. Will be added and set to 'True' if not provided.

    Returns:
        This function returns the modified 'problem' dictionary.
        The following items will have been added:
        * 'D': A numpy array containing the shear force in the cross-section
            at each mm of the beam.
        * 'M': A numpy array containing the bending moment in the cross-section
            at each mm of the beam.
        * 'y': A numpy array containing the vertical displacement at each mm
            of the beam.
        * 'etop': A numpy array containing the strain at the top of the
            cross-section at each mm of the beam.
        * 'ebot': A numpy array containing the strain at the bottom of the
            cross-section at each mm of the beam.
        * 'R': If 'supports' was provided, R is a 2-tuple of the reaction
            forces at said supports. Else R[0] is the reaction force at the
            clamped x=0 and R[1] is the reaction moment at that point.
    """
    length, (s1, s2) = _check_length_supports(problem)
    loads = _check_loads(problem)
    loads = [ld for ld in loads]  # make a copy since we modifiy it!
    EI, GA, top, bot = _check_arrays(problem)
    shear = _check_shear(problem)
    moment = sum([ld.moment(s1) for ld in loads])
    if s2:
        R2 = Load(force=-moment/(s2-s1), pos=s2)
        loads.append(R2)
    else:  # clamped at x = 0
        R2 = -moment
    # Force equilibrium
    R1 = Load(force=-sum([ld.size for ld in loads]), pos=s1)
    loads.append(R1)
    D = np.sum(np.array([ld.shear(length) for ld in loads]), axis=0)
    M = np.cumsum(D)
    if s2 is None:
        M -= M[-1]
    ddy_b = M/EI
    etop, ebot = -top*ddy_b, -bot*ddy_b
    dy = np.cumsum(ddy_b)
    if shear:
        dy += -1.5*D/GA  # shear
    y = np.cumsum(dy)
    if s2:
        # First, translate the whole list so that the value at the
        # index anchor is zero.
        y = y - y[s1]
        # Then rotate around the anchor so that the deflection at the other
        # support is also 0.
        delta = -y[s2]/math.fabs(s1-s2)
        slope = np.concatenate((np.arange(-s1, 1, 1),
                                np.arange(1, len(y)-s1)))*delta
        dy += delta
        y = y + slope
    problem['D'], problem['M'] = D, M
    problem['y'], problem['R'] = y, (R1, R2)
    problem['a'] = np.arctan(dy)
    problem['etop'], problem['ebot'] = etop, ebot
    return problem


class Load(object):
    """Point load."""

    def __init__(self, **kwargs):
        """
        Create a point load.

        Named arguments:
            force: Force in Newtons. N.B: downwards force should be a
                *negative* number.
            kg: Weight of a mass in kg, alternative for force. N.B: a weight
                of 1 kg will translate into a force of -9.81 N.
            pos: Distance from the origin to the location of the force in mm.
        """
        self.size = _force(kwargs)
        self.pos = round(float(kwargs['pos']))

    def __str__(self):
        return "point load of {} N @ {} mm.".format(self.size, self.pos)

    def moment(self, pos):
        """
        Returns the bending moment that the load exerts at pos.
        """
        return (self.pos-pos)*self.size

    def shear(self, length):
        """
        Return the contribution of the load to the shear.

        Arguments:
            length: length of the array to return.

        Returns:
            An array that contains the contribution of this load.
        """
        rv = np.zeros(length+1)
        rv[self.pos:] = self.size
        return rv


class DistLoad(Load):
    """Evenly distributed load."""

    def __init__(self, **kwargs):
        """
        Create an evenly distributed load.

        Named arguments:
            force: Force in Newtons. N.B: downwards force should be a
                *negative* number.
            kg: Weight of a mass in kg, alternative for force. N.B: a weight
                of 1 kg will translate into a force of -9.81 N.
            start: Begin of the distributed load. Must be used in combination
                with the 'end' argument.
            end: End of the distributed load.
            pos: 2-tuple containing the borders of the distributed load.
                You can use this instead of start and end.
        """
        size = _force(kwargs)
        self.start, self.end = _start_end(kwargs)
        if self.start > self.end:
            self.start, self.end = self.end, self.start
        Load.__init__(self, force=size, pos=float(self.start+self.end)/2)

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

    def __init__(self, **kwargs):
        """
        Create an linearly rising distributed load.

        Named arguments:
            force: Force in Newtons. N.B: downwards force should be a
                *negative* number.
            kg: Weight of a mass in kg, alternative for force. N.B: a weight
                of 1 kg will translate into a force of -9.81 N.
            start: Begin of the distributed load. Must be used in combination
                with the 'end' argument.
            end: End of the distributed load.
        """
        DistLoad.__init__(self, **kwargs)
        length = abs(self.start - self.end)
        pos = (self.start, self.end)
        self.pos = round(min(pos)) + 2.0*length/3.0
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


def patientload(**kwargs):
    """
    Returns a list of DistLoads that represent a patient
    load according to IEC 60601 specs. For this calculation the patient is
    assumed to be lying with his feet pointing to the origin.

    Named arguments:
        kg: Mass of the patient in kg.
        force: The gravitational force of the patient in N. Note that this
            should be a *negative* number.
        feet: Location of the patient's feet in mm.
        head: Location of the patient's head in mm. This is an alternative for
            'feet'. Either 'feet' or 'head' must be present or a ValueError
            will be raised.

    Returns:
        A list of DistLoads.
    """
    f = _force(kwargs)
    if 'feet' in kwargs:
        s = round(float(kwargs['feet']))
    elif 'head' in kwargs:
        s = round(float(kwargs['head'])) - 1900
    else:
        raise ValueError("No 'feet' nor 'head' given.")
    fractions = [(0.148*f, (s + 0, s + 450)),  # l. legs, 14.7% from 0--450 mm
                 (0.222*f, (s + 450, s + 1000)),  # upper legs
                 (0.074*f, (s + 1000, s + 1180)),  # hands
                 (0.408*f, (s + 1000, s + 1700)),  # torso
                 (0.074*f, (s + 1200, s + 1700)),  # arms
                 (0.074*f, (s + 1220, s + 1900))]  # head
    return [DistLoad(force=i[0], pos=i[1]) for i in fractions]


def interpolate(tuples):
    """
    Interpolates between tuples.

    Arguments:
        tuples: list of 2-tuples

    Returns:
        a numpy array with interpolated values.
    """
    tuples = sorted(tuples)
    x = np.array([int(round(x)) for x, _ in tuples])
    y = np.array([int(round(y)) for _, y in tuples])
    startx, starty = x[0], y[0]
    arrays = []
    for dx, dy in zip(x[1:] - x[:-1], y[1:] - y[:-1]):
        a = np.linspace(starty, starty + dy, num=dx+1, endpoint=True)
        arrays.append(a[:-1])
        startx += dx
        starty += dy
    arrays.append(np.array([y[-1]]))
    return np.concatenate(arrays)


def _force(kwargs):
    """
    Determine the force. See Load.__init__()

    Returns:
        The force as a float.
    """
    if 'force' in kwargs:
        force = float(kwargs['force'])
    elif 'kg' in kwargs:
        force = -9.81*float(kwargs['kg'])
    else:
        raise KeyError("No 'force' or 'kg' present")
    return force


def _start_end(kwargs):
    """
    Validate the position arguments. See DistLoad.__init_()

    Returns:
        Postition as a (start, end) tuple
    """
    if 'pos' in kwargs:
        p = kwargs['pos']
        if not isinstance(p, tuple) and len(p) != 2:
            raise ValueError("'pos' should be a 2-tuple")
        pos = (round(float(kwargs['pos'][0])), round(float(kwargs['pos'][1])))
    elif 'start' in kwargs and 'end' in kwargs:
        pos = (round(float(kwargs['start'])), round(float(kwargs['end'])))
    else:
        raise KeyError("Neither 'pos' or 'start' and 'end' present")
    return pos


def _check_length_supports(problem):
    """
    Validate that the problem contains proper length and supports. See
    solve().

    Returns:
        A nested tuple (length, (support1, support2))
    """
    problem['length'] = round(problem['length'])
    if problem['length'] < 1:
        raise ValueError('length must be ≥1')
    s = problem['supports']
    if s is not None:
        if len(s) != 2:
            t = 'The problem definition must contain exactly two supports.'
            raise ValueError(t)
        s = (round(s[0]), round(s[1]))
        if s[0] == s[1]:
            raise ValueError('Two identical supports found!')
        elif s[0] > s[1]:
            s = (s[1], s[0])
        if s[0] < 0 or s[1] > problem['length']:
            raise ValueError('Support(s) outside of the beam!')
    else:
        s = (0, None)
    problem['supports'] = s
    return (problem['length'], s)


def _check_loads(problem):
    """
    Validate the loads in the problem. See solve().

    Returns:
        A list of Loads
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
    """
    Validate the length of the EI, GA, top and bot iterables and converts
    them into numpy arrays. This will modify the problem dictionary.
    See solve().

    Returns:
        The modified EI, GA, top and bottom arrays.
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


def _check_shear(problem):
    """
    Check if the problem should incluse shear. See solve().

    Returns:
        The value of problem['shear'].
    """
    if 'shear' not in problem:
        problem['shear'] = True
    elif not isinstance(problem['shear'], bool):
        raise ValueError("'shear' should be a boolean.")
    return problem['shear']
