#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright © 2013 R.F. Smith <rsmith@xs4all.nl>. All rights reserved.
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

"""Module for calculating properties of cross-sections, with a focus
on composite and sandwich structures."""

import math

__version__ = '$Revision$'[11:-2]

def _angle(tp, cp):
    theta1 = math.atan2(tp[0], tp[1])
    theta2 = math.atan2(cp[0], cp[1])
    dtheta = theta2 - theta1
    while dtheta > math.pi:
        dtheta -= 2*math.pi
    while dtheta < -math.pi:
        dtheta += 2*math.pi
    return dtheta


def _checkp(p):
    if isinstance(p, tuple) and len(p) == 2:
        return [p]
    elif (isinstance(p, list) and len(p) > 0 and 
          all([isinstance(j, tuple) for j in p]) and
          all([len(j) == 2 for j in p])):
        return p
    else:
        raise ValueError("p should be a 2-tuple or a list of 2-tuples.")


class Contour(object):
    """Contains a closed contour."""

    def addpoints(self, p):
        """Add one or more points to the contour.

        Arguments:
        p -- point (2-tuple) or a list of points.
        """
        if self.closed:
            raise ValueError("Contour is already closed")
        p = _checkp(p)
        self.points += [(float(i[0]), float(i[1])) for i in p]
        x = [i[0] for i in self.points]
        y = [i[1] for i in self.points]
        self.bbox = (min(x), max(y), max(x), min(y))
        if self.points[0] == self.points[-1]:
            del self.points[-1]
            self.closed = True

    def __init__(self, p=None):
        """Create a Contour. If a list of points is given, use that as
        the boundaries of the contour.

        Arguments:
        p -- initial point (2-tuple) or a list of points.
        """
        self.closed = False
        self.points = []
        self.bbox = (None, None, None, None) # left, top, right, bottom
        if p:
            self.addpoints(p) 

    def inside(self, p):
        """Check if one or more points are inside of the contour.

        Arguments:
        p -- point (2-tuple) or a list of points.
        """
        if not self.closed:
            raise ValueError('Contour must be closed.')
        res = []
        p = _checkp(p)
        for i in p: # Check first if it is outside the bounding box
            if (i[0] < self.bbox[0] or i[1] > self.bbox[1] or  
                i[0] > self.bbox[2] or i[1] < self.bbox[3]):
#                print 'Outside of bounding box!'
                res.append(False)
            else:
                vecs = [(i[0]-j[0], i[1]-j[1]) for j in self.points]
                ang = [_angle(vecs[i+1], vecs[i]) for i in 
                       xrange(len(vecs)-1)]
#                print 'sum of angles:', sum(ang)
                if sum(ang) < math.pi:
                    res.append(False)
                else:
                    res.append(True)
        if len(res) == 1:
            return res[0]
        return res

    def all_inside(self, other):
        return all(self.inside(other.points))

    def intersect(self, other):
        if True in self.inside(other.points):
            return True
        return False

    def ipoints(self, y):
        rv = []
        if y > self.bbox[1] or y < self.bbox[3]:
            return rv
        for i in xrange(len(self.points-1)):
            xp = [self.points[i][0], self.points[i+1][0]]
            yp = [self.points[i][1], self.points[i+1][1]]
            if y < min(yp) or y > max(yp):
                continue
            dx = xp[0] - xp[1]
            dy = yp[0] - yp[1]
            


class Xsec(object):
    
    def __init__(self):
        self.contours = []


    def addcontour(self, c, E, G):
        if not isinstance(c, Contour) and not c.closed:
            raise ValueError('must provide a closed contour object')
        self.contours.append((c, float(E), float(G)))
    
    def addhole(self, c):
        self.addcontour(c, 0.0, 0.0)
