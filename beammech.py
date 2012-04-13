#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2012 R.F. Smith <rsmith@xs4all.nl>. All rights reserved.
# Time-stamp: <2012-04-13 18:33:01 rsmith>
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

def pointload(length, loadspec, supports):
    '''Calculates a list of shear forces based on a single point load. The
    list has a resolution of 1 mm per list unit. The shear force at index p 
    exists over the domain from p to p+1.

    - length: length of the product in millimeters.
    - loadspec: a 2-tuple (location [mm], magnitude [N]) of the pointload.
    - supports: a 2-tuple of the location in mm of the supports.'''
    assert len(loadspec) == 2, 'Loadspec must be a 2-tuple (location, magnitude)'
    assert len(supports) == 2, 'There must be two supports.'
    assert -1<supports[0]<=length, 'The first support lies outside the beam.'
    assert -1<supports[1]<=length, 'The second support lies outside the beam'
    R3 = -math.fabs(loadspec[1])
    s1 = min(supports) # Reaction force R1 applies here.
    s2 = max(supports) # Reaction force R2 applies here.
    s3 = loadspec[0]
    rv = [0.0 for index in range(0,length+1)]
    R2 = -R3*float(s3-s1)/float(s2-s1)
    R1 = -R3-R2
    if s2 > s3:
        R3,R2 = R2,R3
        s3,s2 = s2,s3
    rv[s1:s2] = [R1]*(s2-s1)
    rv[s2:s3] = [R1+R2]*(s3-s2)
    return rv

def integrate(src):
    '''Integrates a list of values. No integration constants!'''
    rv = [0.0]
    for i in range(len(src)-1):
        rv.append(rv[-1]+src[i])
    return rv

def align(src, supports):
    '''Transform a list of values such that the value at the supports is zero.'''
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
    respectively. 
    - supports: A list of positions of the two supports
    Returns a tuple of three lists containing the deflection, 
    maximum tensile stress and maximum compression stress.'''
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
    pass
