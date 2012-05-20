#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2012 R.F. Smith <rsmith@xs4all.nl>. All rights reserved.
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
        - size: force in Newtons
        - pos: distance of the force from the origin in mm.'''
        assert pos >= 0, 'Positions must be positive.'
        self.size = float(size)
        self.pos = pos

    def __str__(self):
        return "point load of {} N @ {} mm.".format(self.size, self.pos)

    def moment(self, pos):
        '''Calculate the bending moment the load exerts at pos.'''
        assert pos >= 0
        return (self.pos-pos)*self.size

    def shear(self, pos):
        '''Returns the contribution of the load to the shear at pos.'''
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

def kg2N(k):
    '''Converts kilograms to Newtons.'''
    return float(k)*9.81

def shearforce(length, loads, supports):
    '''Calculates a list of shear forces based on a list of loads. The
    returned list has a resolution of 1 mm per list unit. The shear force at
    index p exists over the domain from p to p+1.

    - length: length of the product in millimeters.
    - loads: list of Loads.
    - supports: a 2-tuple of the location in mm of the supports.
    
    Returns a 3-tuple consisting of a list of shear values, 
    reaction Load R1 and reaction Load R2.
    '''
    length = int(length)
    assert length > 0, 'Beam of negative length is impossible.'
    if isinstance(loads, list):
        assert len(loads) > 0, 'No loads specified'
        for ld in loads:
            assert ld.pos >= 0 and ld.pos <= length, 'Load outside length'
    else:
        assert isinstance(loads, Load)
        loads = [loads]
    assert len(supports) == 2, 'There must be two supports.'
    assert 0 <= supports[0] <= length
    assert 0 <= supports[1] <= length
    s1 = min(supports) # Reaction force R1 applies here.
    s2 = max(supports) # Reaction force R2 applies here.
    # Moment balance around s1
    moments = sum([ld.moment(s1) for ld in loads])
    R2 = Load(-moments/(s2-s1), s2)
    loads.append(R2)
    # Force equilibrium
    R1 = Load(-sum([ld.size for ld in loads]), s1)
    loads.append(R1)
    xvals = range(length)
    contribs = []
    for ld in loads:
        contribs.append([ld.shear(x) for x in xvals])
    rv =  map(sum, zip(*contribs))
    rv.append(0.0)
    return (rv, R1, R2)

def _integrate(src):
    '''Integrates a list of values. No integration constants!'''
    assert len(src) > 0
    rv = [0.0]
    for i in range(len(src)-1):
        rv.append(rv[-1]+src[i])
    return rv

def _supcheck(src, spts):
    '''Check the supports argument.'''
    assert len(spts) == 2, 'There must be two supports!'
    if isinstance(spts[0], Load):
        rv = [spts[0].pos, spts[1].pos]
    else:
        rv = [int(spts[0]), int(spts[1])]
    assert 0 <= rv[0] <= len(src), 'The first support lies outside the beam.'
    assert 0 <= rv[1] <= len(src), 'The second support lies outside the beam.'
    return rv

def _align(src, supports):
    '''Transform a list of values such that the value at the supports is 
    zero.'''
    assert len(src) > 0
    supports = _supcheck(src, supports)
    anchor = supports[0]
    # First, translate the whole list so that the value at the 
    # index anchor is zero.
    translated = [src[i]-src[anchor] for i in range(len(src))]
    # Then rotate around the anchor so that the deflection at the other
    # support is also 0.
    delta = translated[supports[1]]/math.fabs(supports[0]-supports[1])
    rv = [translated[i]-delta*(i-anchor) for i in range(len(src))]
    return rv

def loadcase(D, E, xsecprops, supports, shear=True):
    '''Calculates a loadcase.
    - D: list of shear force values along the length of the beam.
    - E: Young's Modulus of the homogenized beam,
    - xsecprops: function that takes a single position argument and returns 
    a four-tuple (I, GA, etop, ebot) of the cross-section at that position. 
    The I is the second area moment of the homogenized cross-section in mm⁴. 
    GA is the shear stiffness in N. The e* values are the distance from the 
    neutral line of the cross-section to the top and bottom of the material 
    in mm respectively. The latter should be negative.
    - supports: A list of positions of the two supports
    Returns a tuple of four lists containing the bending moment, deflection, 
    stress at the top and stress at the bottom of the cross-section.
    -shear: Indicates wether shear deflection should be taken into
    account. True by default.'''
    supports = _supcheck(D, supports)
    M = _integrate(D)
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
    y_tot = _align(y_tot, supports)
    return (M, y_tot, top, bottom)
