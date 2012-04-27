#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2012 R.F. Smith <rsmith@xs4all.nl>. All rights reserved.
# Time-stamp: <2012-04-27 16:37:38 rsmith>
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

"Test case based on AD5 tabletop."

import beammech

def xsecprops_test(x):
    B = 400.0
    H = 40.0
    h = H-4
    I= B*(H**3-h**3)/12.0
    GA = (4350*2*H)+(B*h*8)
    return (I, GA, 20.0, -20.0)

def belastingsgeval1():
    E = 0.5*240000
    L = 1000
    F = -500
    oplegpunten = (0, L)
    P = beammech.Load(F, L/2)
    D, Ra, Rb =  beammech.shearforce(L, P, oplegpunten)
    y, t, b = beammech.loadcase(D, E, xsecprops_test, oplegpunten, False)
    print 'Belastingsgeval 1, {}'.format(P)
    res = xsecprops_test(0)
    print res
    print 'Verplaatsing zuivere buiging volgens integratie {:.1f} mm,'.format(y[500])
    print 'Verplaatsing zuivere buiging volgens formule {:.1f} mm.'.format(F*L**3/(48*res[0]*E))
    y, t, b = beammech.loadcase(D, E, xsecprops_test, oplegpunten)
    print 'Verplaatsing buiging en afschuiving volgens integratie {:.1f} mm.\n'.format(y[500])


if __name__ == '__main__':
    belastingsgeval1()
