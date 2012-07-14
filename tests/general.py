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

"Test cases for beammech."

import beammech

E = 0.5*240000 # Young's Modulus of the beam's material in [MPa]
L = 1000 # Length of the beam in [mm]
F = -500 # Force in [N]

def xsecprops_test(x):
    '''Section properties for test cases.'''
    B = 400.0
    H = 40.0
    h = H-4
    I= B*(H**3-h**3)/12.0
    GA = (4350*2*H)+(B*h*8)
    return (I, GA, 20.0, -20.0)

def loadcase1():
    '''Point load in the middle of a beam that is supported at both ends.'''
    global E, L, F
    supports = (0, L)
    P = beammech.Load(F, L/2)
    # Calculate the shear force in the cross-section every [mm], 
    # and the reaction forces at the supports.
    D, Ra, Rb =  beammech.shearforce(L, P, supports)
    # Calculate the load case without shear deflection.
    M, y, t, b = beammech.loadcase(D, E, xsecprops_test, supports, False)
    print 'Loadcase 1, {}'.format(P)
    res = xsecprops_test(0)
    print 'Deflection under pure bending [beammech]: {:.2f} mm.'.format(y[500])
    st = 'Deflection under pure bending [formula]: {:.2f} mm.'
    print st.format(F*L**3/(48*res[0]*E))
    # Calculate the load case with shear deflection.
    M, y, t, b = beammech.loadcase(D, E, xsecprops_test, supports)
    st = 'Deflection under pure bending and shear [beammech]: {:.2f} mm.\n'
    print st.format(y[500])

def loadcase2():
    '''Distributed load over the whole beam that is supported at both ends.'''
    global E, L, F
    supports = (0, L)
    P = beammech.DistLoad(F, (0,L))
    # Calculate the shear force in the cross-section every [mm], 
    # and the reaction forces at the supports.
    D, Ra, Rb =  beammech.shearforce(L, P, supports)
    # Calculate the load case without shear deflection.
    M, y, t, b = beammech.loadcase(D, E, xsecprops_test, supports, False)
    print 'Loadcase 2, {}'.format(P)
    res = xsecprops_test(0)
    print 'Deflection under pure bending [beammech]: {:.2f} mm.'.format(y[500])
    st = 'Deflection under pure bending [formula]: {:.2f} mm.'
    print st.format(5*F*L**3/(384*res[0]*E))
    # Calculate the load case with shear deflection.
    M, y, t, b = beammech.loadcase(D, E, xsecprops_test, supports)
    st = 'Deflection under pure bending and shear [beammech]: {:.2f} mm.\n'
    print st.format(y[500])

def loadcase3():
    '''Triangle load over the whole beam that is supported at both ends.'''
    global E, L, F
    maxx = int(0.519*L)
    supports = (0, L)
    P = beammech.TriangleLoad(F, (0,L))
    # Calculate the shear force in the cross-section every [mm], 
    # and the reaction forces at the supports.
    D, Ra, Rb =  beammech.shearforce(L, P, supports)
    # Calculate the load case without shear deflection.
    M, y, t, b = beammech.loadcase(D, E, xsecprops_test, supports, False)
    print 'Loadcase 3, {}'.format(P)
    res = xsecprops_test(0)
    print 'Deflection under pure bending [beammech]: {:.2f} mm.'.format(y[maxx])
    st = 'Deflection under pure bending [formula]: {:.2f} mm.'
    print st.format(0.01304*F*L**3/(res[0]*E))
    M, y, t, b = beammech.loadcase(D, E, xsecprops_test, supports)
    st = 'Deflection under pure bending and shear [beammech]: {:.2f} mm.\n'
    print st.format(y[maxx])


if __name__ == '__main__':
    loadcase1()
    loadcase2()
    loadcase3()
