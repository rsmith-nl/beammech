#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2012,2013 R.F. Smith <rsmith@xs4all.nl>. All rights reserved.
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
# THIS SOFTWARE IS PROVIDED BY AUTHOR AND CONTRIBUTORS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED.  IN NO EVENT SHALL AUTHOR OR CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.

"Module for simple stiffness and strength calculations of beams."

import math

__version__ = '$Revision$'[11:-2]

class Load(object):
    '''Point load.'''

    def __init__(self, size, pos):
        '''Create a point load.

        Arguments
        size -- force in Newtons.
        pos -- distance of the force from the origin in mm.
        '''
        if pos < 0:
            raise ValueError('Positions must be positive.')
        self.size = float(size)
        self.pos = int(pos)

    def __str__(self):
        return "point load of {} N @ {} mm.".format(self.size, self.pos)

    def moment(self, pos):
        '''Returns the bending moment the load exerts at pos.
        '''
        assert pos >= 0
        return (self.pos-pos)*self.size

    def shear(self, pos):
        '''Returns the contribution of the load to the shear at pos.
        '''
        assert pos >= 0
        if pos < self.pos:
            return 0.0
        return self.size

class DistLoad(Load):
    '''Evenly distributed load.'''

    def __init__(self, size, pos):
        assert pos[0] >= 0 and pos[1] >= 0 
        self.start = int(min(pos))
        self.end = int(max(pos))
        Load.__init__(self, size, float(self.start+self.end)/2)

    def __str__(self):
        r = "constant distributed load of {} N @ {}--{} mm."
        return r.format(self.size, self.start, self.end)

    def moment(self, pos):
        assert pos >= 0
        if pos <= self.start or pos >= self.end:
            return Load.moment(self, pos)
        left = float(pos-self.start)
        right = float(self.end-pos)
        length = float(self.end-self.start)
        return (left**2-right**2)*self.size/(2*length)

    def shear(self, pos):
        assert pos >= 0
        if pos <= self.start:
            return 0.0
        if pos >= self.end:
            return self.size
        extent = float(self.end - self.start)
        offs = float(pos - self.start)
        return self.size*offs/extent

class TriangleLoad(DistLoad):
    '''Linearly rising distributed load.'''

    def __init__(self, size, pos):
        DistLoad.__init__(self, size, pos)
        q = 2.0*size/((pos[1]-pos[0])**2)
        L = max(pos)-min(pos)
        self.pos = min(pos)+2.0*L/3.0
        if pos[0] < pos[1]:
            self.V = [q*(i+0.5) for i in xrange(0, L)]
        elif pos[0] > pos[1]:
            self.V = [q*(i-0.5) for i in xrange(L, 0, -1)]
        else:
            raise ValueError

    def __str__(self):
        r = "linearly {} distributed load of {} N @ {}--{} mm."
        if self.start < self.end:
            direction = 'ascending'
        else:
            direction = 'descending'
        return r.format(direction, self.size, self.start, self.end)

    def moment(self, pos):
        assert pos >= 0
        d = self.start-pos
        return sum([(d+i+0.5)*self.V[i] for i in xrange(0, len(self.V))])

    def shear(self, pos):
        assert pos >= 0
        if pos < self.start:
            return 0.0
        if pos > self.end:
            return self.size
        frac = pos-self.start+1
        return sum(self.V[0:frac])


def patientload(mass, s):
    '''Returns a list of DistLoads that represent a patient
    load according to IEC 60601 specs.

    Argument:
    mass -- mass of the patient in kg.
    s -- location of the feet in mm. Head lies at s+1900.
    '''
    f = -kg2N(mass)
    fractions = [(0.148*f, (s + 0, s + 450)), # l. legs, 14.7% from 0 to 450 mm.
                 (0.222*f, (s + 450, s + 1000)), # upper legs
                 (0.074*f, (s + 1000, s + 1180)), # hands
                 (0.408*f, (s + 1000, s + 1700)), # torso
                 (0.074*f, (s + 1200, s + 1700)), # arms
                 (0.074*f, (s + 1220, s + 1900))] #head
    return [DistLoad(i[0], i[1]) for i in fractions]


def kg2N(k):
    '''Converts kilograms to Newtons.'''
    return float(k)*9.81


def shearforce(length, loads, supports=None):
    '''Calculates a list of shear forces based on a list of loads. The
    returned list has a resolution of 1 mm per list unit. The shear
    force at index p exists over the domain from p to p+1.

    Returns a 3-tuple consisting of a list of shear values, reaction
    Load R1 and either Load R2 for a simple support or reaction moment
    R1 when clamped.

    Arguments:
    length -- length of the product in millimeters.
    loads -- list of Loads.
    supports -- a 2-tuple of the location in mm of the supports, or
    None if the beam is clamped at x=0.
    '''
    length = int(length)
    assert length > 0, 'Beam of negative length is impossible.'
    if isinstance(loads, list):
        if len(loads) == 0:
            raise ValueError('No loads specified')
        for ld in loads:
            assert ld.pos >= 0 and ld.pos <= length, 'Load outside length'
    elif isinstance(loads, Load):
        loads = [loads]
    else:
        raise ValueError('Not a Load or a list of Loads')
    s1, s2 = _supcheck(length, supports)
    # Moment balance around s1
    moments = sum([ld.moment(s1) for ld in loads])
    if s2:
        R2 = Load(-moments/(s2-s1), s2)
        loads.append(R2)
    else:
        R2 = moments
    # Force equilibrium
    R1 = Load(-sum([ld.size for ld in loads]), s1)
    loads.append(R1)
    xvals = range(length)
    contribs = []
    for ld in loads:
        contribs.append([ld.shear(x) for x in xvals])
    rv =  map(sum, zip(*contribs)) # pylint: disable=W0141
    rv.append(0.0)
    return (rv, R1, R2)


def _integrate(src):
    '''Integrates a list of values. Does not use integration constants!
    '''
    if len(src) == 0:
        raise ValueError('Nothing to integrate')
    rv = [0.0]
    for i in range(len(src)-1):
        rv.append(rv[-1]+src[i])
    return rv


def _supcheck(length, spts):
    '''Check the supports argument.'''
    if spts == None:
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


def _align(src, s1, s2):
    '''In the situation with two supports, transform a list of values such
    that the value at the supports is zero.
    '''
    assert len(src) > 0
    if s2 is None:
        return src
    anchor = s1
    # First, translate the whole list so that the value at the 
    # index anchor is zero.
    translated = [src[i]-src[anchor] for i in range(len(src))]
    # Then rotate around the anchor so that the deflection at the other
    # support is also 0.
    delta = translated[s2]/math.fabs(s1-s2)
    rv = [translated[i]-delta*(i-anchor) for i in range(len(src))]
    return rv


def loadcase(D, E, xsecprops, supports=None, shear=True):
    '''Calculates a loadcase.

    Returns a tuple of four lists containing the bending moment,
    deflection, stress at the top and stress at the bottom of the
    cross-section.

    Arguments:
    D -- list of shear force values along the length of the beam.
    E -- Young's Modulus of the homogenized beam,
    xsecprops -- function that takes a single position argument and returns 
    a four-tuple (I, GA, etop, ebot) of the cross-section at that position.
    The I is the second area moment of the homogenized cross-section in mm⁴. 
    GA is the shear stiffness in N. The e* values are the distance from the 
    neutral line of the cross-section to the top and bottom of the material 
    in mm respectively. The latter should be negative.
    supports -- A list of positions of the two supports, or None of
    the beam is clamped at x=0.
    shear -- Indicates wether shear deflection should be taken into
    account. True by default.

    '''
    s1, s2 = _supcheck(D, supports)
    M = _integrate(D)
    if s2 is None:
        mr = M[-1]
        M = [j-mr for j in M]
    xvals = range(len(D))
    I, GA, etop, ebot = zip(*[xsecprops(x) for x in xvals])
    top = [-M[x]*etop[x]/I[x] for x in xvals]
    bottom = [-M[x]*ebot[x]/I[x] for x in xvals]
    ddy_b = [M[x]/(E*I[x]) for x in xvals]
    dy_b = _integrate(ddy_b)
    if shear:
        dy_sh = [-1.5*D[x]/GA[x] for x in xvals]
        dy_tot = [i+j for i, j in zip(dy_b, dy_sh)]
    else:
        dy_tot = dy_b
    y_tot = _integrate(dy_tot)
    y_tot = _align(y_tot, s1, s2)
    return (M, y_tot, top, bottom)


def calculate(length, loads, E, xsecprops, supports=None, shear=True):
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
    M, y, st, sb = loadcase(D, E, xsecprops, supports, shear)
    return D, M, y, st, sb, R1, R2
