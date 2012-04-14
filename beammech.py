#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2012 R.F. Smith <rsmith@xs4all.nl>. All rights reserved.
# Time-stamp: <2012-04-14 21:40:03 rsmith>
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
        '''Calculate the bending moment the force exerts at pos.'''
        assert pos >= 0
        return (self.pos-pos)*self.size

    def shear(self, pos):
        '''Returns the contribution to the shear load at pos.'''
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
        rs = "distributed load of {} N @ {}--{} mm."
        return rs.format(self.size, self.start, self.end)

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

def kg(v):
    '''Converts kilograms to Newtons.'''
    return float(v)*9.81

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
    assert len(loads) > 0, 'No loads specified'
    for ld in loads:
        assert ld.pos >= 0 and ld.pos <= length, 'Load outside length'
    assert len(supports) == 2, 'There must be two supports.'
    assert 0 <= supports[0] <= length
    assert 0 <= supports[1] <= length
    s1 = min(supports) # Reaction force R1 applies here.
    s2 = max(supports) # Reaction force R2 applies here.
    # Moment balance around s1
    moments = sum([ld.moment(s1) for ld in loads])
    #print [ld.moment(s1) for ld in loads]
    #print moments
    R2 = Load(-moments/(s2-s1), s2)
    loads.append(R2)
    # Force equilibrium
    R1 = Load(-sum([ld.size for ld in loads]), s1)
    loads.append(R1)
    xvals = range(length)
    contribs = []
    for ld in loads:
        contribs.append(map(ld.shear, xvals))
    print contribs
    rv =  map(sum, zip(*contribs))
    rv.append(0.0)
    return (rv, R1, R2)

def integrate(src):
    '''Integrates a list of values. No integration constants!'''
    assert len(src) > 0
    rv = [0.0]
    for i in range(len(src)-1):
        rv.append(rv[-1]+src[i])
    return rv

def align(src, supports):
    '''Transform a list of values such that the value at the supports is zero.'''
    assert len(src) > 0
    assert len(supports) == 2, 'There must be two supports!'
    assert -1<supports[0]<=len(src), 'The first support lies outside the beam.'
    assert -1<supports[1]<=len(src), 'The second support lies outside the beam.'
    anchor = supports[0]
    # First, translate the whole list so that the value at the 
    # index anchor is zero.
    translated = [src[i]-src[anchor] for i in range(len(src))]
    # Then rotate around the anchor so that the deflection at the other
    # support is also 0.
    delta = translated[supports[1]]/math.fabs(supports[0]-supports[1])
    rv = [translated[i]-delta*(i-anchor) for i in range(len(src))]
    return rv

def loadcase(D, E, xsecprops, supports):
    '''Calculates a loadcase.
    - D: list of shear force values along the length of the beam.
    - E: Young's Modulus of the homogenized beam,
    - xsecprops: function that takes a single position argument and returns 
    a four-tuple (I, GA, etop, ebot) of the cross-section at that position. 
    The I is the second area moment of the homogenized cross-section in mm⁴. 
    GA is the shear stiffness in N. The e* values are the distance from the 
    neutral line of the cross-section to the top and bottom of the material 
    in mm respectively. 
    - supports: A list of positions of the two supports
    Returns a tuple of three lists containing the deflection, 
    maximum tensile stress and maximum compression stress.'''
    assert len(supports) == 2, 'There must be two supports!'
    assert -1<supports[0]<=len(D), 'The first support lies outside the beam.'
    assert -1<supports[1]<=len(D), 'The second support lies outside the beam.'
    M = integrate(D)
    xvals = range(len(D))
    I, GA, etop, ebot = zip(*map(xsecprops, xvals))
    tension = map(lambda x: -M[x]*etop[x]/I[x], xwaardes)
    compression = map(lambda x: -M[x]*ebot[x]/I[x], xwaardes)
    ddy_b = map(lambda i: -M[i]/(E*I[i]), xvals)
    dy_b = integrate(ddy_b)
    dy_sh = map(lambda i: 1.5*D[i]/GA[i], xvals)
    dy_tot = map(lambda x,y: x+y, dy_b, dy_sh)
    y_tot = integrate(dy_tot)
    y_tot = align(y_tot, supports)
    return (y_tot, tension, compression)

# Tests
if __name__ == '__main__':
    PL1 = Load(-1, 9)
    print PL1
    DL1 = DistLoad(-5, [3, 8])
    print DL1
    print 'should be 0:', DL1.moment(5.5)
    print 'should be negative:', DL1.moment(3)
    print 'should be positive:', DL1.moment(8)
    D, P, Q = shearforce(10, [PL1, DL1], [0,5])
    print "Sum of forces:", PL1.size + DL1.size + P.size + Q.size
    print 'Sum of moments:', (PL1.moment(0) + DL1.moment(0) + 
                              P.moment(0) + Q.moment(0))
    print P
    print Q
    print D
