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

"Test case based on AD5 tabletop."

import beammech

def xsecprops_AD5(x):
    '''Geeft de eigenschappen van het AD5-blad op punt x, in de vorm van een 
    tuple (traagheidsmoment, afschuifstijfheid, randafstand boven, 
    randafstand onder).'''
    GA_schuim = 8.0*13903.0
    GA_prof = 25000.0*(2*2653)
    GA_lam = 4350.0*(2*2.0*36.5)
    GA_kop = 4350.0*(4.0*500)
    if x < 1672: # Gedeelte met profielen
        return (4104890.0, GA_schuim+GA_prof+GA_lam, 30.78, -9.01)
    elif x < 2655: # Metaalvrije sandwich
        return (575328.0, GA_schuim+GA_lam, 18.68, -21.12)
    return (2282.0, GA_kop, 2.0, -2.0) # Kopstuk

def belastingsgeval1():
    '''Deflectie op krachtaangrijpingspunt bij P = 1000 N.'''
    oplegpunten = (32, 1652)
    P = beammech.Load(-1000, 2522)
    D, Ra, Rb =  beammech.shearforce(2930, P, oplegpunten)
    M, y, t, c = beammech.loadcase(D, 70000.0, xsecprops_AD5, oplegpunten)
    rs = 'Belastingsgeval 1, {}\n({} mm van einde profiel.)'
    print rs.format(P, 2522-1620-32)
    print 'Berekende verplaatsing {:.1f} mm,'.format(y[2522])
    print 'Toegstane verplaatsing -12.4 mm.\n'
    of = open('AD5-1.d', 'w')
    of.write('# Deflectie bij P = 1000 N.\n')
    for x,F in enumerate(D):
        of.write('{} {}\n'.format(x, y[x]))
    of.close()

def belastingsgeval2():
    '''Spanning in laminaat bij einde profielen bij puntlast.'''
    P = -4e6/870.0
    oplegpunten = (32, 1652)
    P = beammech.Load(P, 2522)
    D, Ra, Rb =  beammech.shearforce(2930, P, oplegpunten)
    M, y, t, b = beammech.loadcase(D, 70000.0, xsecprops_AD5, oplegpunten)
    of = open('AD5-2.d', 'w')
    of.write('# Spanningen bij P = {} N.\n'.format(P))
    for x,F in enumerate(D):
        of.write('{} {} {}\n'.format(x, t[x], b[x]))
    of.close()
    rs = 'Belastingsgeval 2, {}\n({} mm van einde profiel.)'
    print rs.format(P, 2522-1620-32)
    print 'Maximale spanningen in het laminaat bij het einde van de profielen;'
    rs = '{}: {:.0f} MPa, {:.0f} MPa'
    print rs.format('Optredend einde metaalvrije deel', t[1673],  b[1673])
    print rs.format('Optredend net tussen de profielen', t[1671],  b[1671])
    druklimiet = -0.5*(73943*8*20)**(1/3.0)
    print rs.format('Toegestaan', 0.02*73943,  druklimiet)
    print

def belastingsgeval3():
    '''Impact belasting van 225 kg van 150 mm hoogte op 650 mm van hoofdeinde.'''
    T = -beammech.kg2N(225)
    pos = 2930-650
    print 'Belastingsgeval 3'
    rs = 'Dynamische valtest van {} kg ({} N) op 650 mm van hoofdeinde (x={}).'
    print rs.format(225, T, pos)
    oplegpunten=(37, 450+37)
    for F in range(-10000, -30000, -10):
        P = beammech.Load(F, pos)
        D, Ra, Rb =  beammech.shearforce(2930, P, oplegpunten)
        M, y, t, b = beammech.loadcase(D, 70000.0, xsecprops_AD5, oplegpunten)
        elastische_energie = 0.5*P.size*y[pos]
        impact = T*(-150+y[pos])
        if elastische_energie >= impact:
            break
    print 'De dynamische valtest komt qua energie overeen met'
    rs = 'een statische last van {} N op 650 mm van het hoofdeinde.'
    print rs.format(P.size)
    print '({})'.format(P)
    print 'deflectie @ {} mm: {:.1f} mm'.format(pos, y[pos])
    print 'Ra', Ra
    print 'Rb', Rb
    print 'Maximale spanningen in het laminaat bij het einde van de profielen;'
    rs = '{}: {:.0f} MPa, {:.0f} MPa'
    print rs.format('Optredend einde metaalvrije deel', t[1673],  b[1673])
    print rs.format('Optredend net tussen de profielen', t[1671],  b[1671])
    druklimiet = -0.5*(73943*8*20)**(1/3.0)
    print rs.format('Toegestaan', 0.02*73943,  druklimiet)
   
if __name__ == '__main__':
    belastingsgeval1()
    belastingsgeval2()
    belastingsgeval3()
