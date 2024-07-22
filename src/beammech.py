# file: beammech.py
# vim:fileencoding=utf-8:ft=python:fdm=marker
# Copyright © 2012-2020 R.F. Smith <rsmith@xs4all.nl>. All rights reserved.
# SPDX-License-Identifier: MIT
# Last modified: 2024-07-22T20:02:09+0200
#
"""
Beammech is a package for solving the differential equations for pure bending
d²y/dx² = M/(E·I) and shear dy/dx = α·V/(G·A) of beams.

The main interface is the ``solve`` function. It returns a ``types.SimpleNamespace``.
Saving the returned information to file is done with the ``save`` function.

Before we can solve the problem we need to define it.
The length of the beam and the location of the supports are the initial
parameters.

.. code-block:: python

    import beammech as bm

    beam = {}
    length = 2287
    supports = (6, 780)

The length and the locations of the supports will be rounded to the
nearest integer.  The beam will stretch from x = 0 to x = length.  The value
of ``supports`` must be a 2-tuple of integers or ``None``.  If necessary the
supports will be placed into ascending order.  The beam is assumed to be simply
supported at the two support points.  This means that vertical movement of
those points is prescribed as 0, but rotation of the beam around those points
is not restricted.  If the value of supports is ``None``, the beam is assumed to
be clamped at x=0.

We need to define some loads on the beam.  Several types of load are defined,
all of them acting in the y-direction.

* Point load
* Distributed load
* Triangle load; starts at 0 and rises linearly to the end. The force given is
  the total load.

Rather than being concentrated at a single location, a distributed load is
evenly spread out between its start and end positions.  You can think of it as
a small point load on every mm between the start and end points.  The sum of
all those small loads is the given load.  The triangle load starts at zero and
rises linearly to the end point.  Again the force given is the sum of all
small loads on the intermediate points.  Loads are created using keyword
arguments. The magnitude of the load can be given one of several keywords;

* force: a force in Newtons
* kg: a mass in kg

The mass in kg is converted to a force in Newtons.  Standard Earth gravity is
used in the -y direction (-9.81 m/s²).

.. code-block:: python

    L1 = bm.PointLoad(force=-2000, pos=1000)
    L2 = bm.DistLoad(kg=50, start=1500, end=2000)
    L3 = bm.TriangeLoad(force=-200, start=1500, end=1200)

These is a function called “patientload” which creates a list of DistLoad
objects forming the standard weight distribution of a human body according to
IEC 60601.  The length of the standard patient is 1900 mm.  The feet of the
patient point to x = 0.  The mass of the patient is specified in kg and either
the location of the feet or the head of the patient can be given.

.. code-block:: python

    L4 = bm.patientload(kg=250, head=2287)
    L4 = bm.patientload(kg=280, feet=1200)

The loads are added to the problem definition in the form of a single load or
in the form of an iterable of loads.

.. code-block:: python

    loads = [L1, L2, L3]

The only thing missing now to characterize the beam completely are the bending
stiffness E·I, the shear stiffness G·A and the distance from the neutral line
to the top and bottom of the beam at each mm along the length of the beam.
Calculating these properties can be difficult for beams made out of different
materials (e.g. sandwich structures).  For every point in the length the
products E·I, G·A and the top- and bottom distance from the neutral line are
gathered in a numpy array and added to the problem dictionary.  In the example
below a constant rectangular cross-section is used for simplicity.  But it is
in the composition of these arrays that you can construct basically any
variation in beam geometry.

.. code-block:: python

    import numpy as np

    E = 69500  # Young's modulus of aluminium [MPa]
    G = 26000  # shear modulus of aluminium [MPa]
    B, H = 30, 3
    I, A = B*H**3/12, B*H
    n = length+1
    EI = np.ones(n)*E*I
    GA = np.ones(n)*G*A
    top = np.ones(n)*H/2
    bot = np.ones(n)*-H/2

Observe that the length of the numpy arrays needs to be one more than the
length of the beam, because it must contain values from 0 up to *and
including* the length.

Having gathered all the data for the problem, be can now let the software
solve it.

.. code-block:: python

    results = bm.solve(length, supports, EI, GA, top, bottom, True)

This will raise a KeyError if values are missing from the problem definition,
or a ValueError if incorrect values are used.  On successful completion, the
results are returned in a dictionary.  The following keys exist;

'D'
    A numpy array containing the shear force in the cross-section at each mm
    of the beam.

'M'
    A numpy array containing the bending moment in the cross-section at each mm
    of the beam.

'y'
    A numpy array containing the vertical displacement at each mm of the beam.

'a'
    A numpy array containing angle between the tangent line of the beam and the
    x-axis in radians at each mm of the beam.

'etop'
    A numpy array containing the strain at the top of the cross-section at
    each mm of the beam.

'ebot'
    A numpy array containing the strain at the bottom of the cross-section at
    each mm of the beam.

'R'
    If 'supports' was provided, R is a 2-tuple of the reaction forces at said
    supports. Else R[0] is the reaction force at the clamped x=0 and R[1] is
    the reaction moment at that point
"""

from datetime import datetime
from os.path import basename
from types import SimpleNamespace
import math
import numpy as np

__version__ = "2020.10"


def solve(length, supports, loads, EI, GA, top, bottom, shear):  # {{{
    """Solve the beam problem.

    Arguments:
        length: The length of the beam in mm. This will be rounded to
            an integer value.
        supports: Either None or a 2-tuple of numbers between 0 and length.
            If None, the beam will be assumed to be clamped at the origin.
        loads: Either a Load or an iterable of Loads.
        EI: An iterable of size length+1 or a float containing the bending
            stiffenss in every mm of the cross-section of the beam.
        GA: An iterable of size length+1 or a float containing the shear
            stiffenss in every mm of the cross-section of the beam.
        top: An iterable of size length+1 or a float containing the height
            above the neutral line in every mm of the cross-section of the beam.
        bottom: An iterable of size length+1 or a float containing the height
            under the neutral line in every mm of the cross-section of the beam.
        shear: A boolean indication if shear deformations should be
             included. Will be added and set to 'True' if not provided.

    Returns:
        This function returns a types.SimpleNamespace with following items:
        * D: A numpy array containing the shear force in the cross-section
            at each mm of the beam.
        * M: A numpy array containing the bending moment in the cross-section
            at each mm of the beam.
        * dy: A numpy array containing the deflection angle at each mm
            of the beam.
        * y: A numpy array containing the vertical displacement at each mm
            of the beam.
        * a: A numpy array containing angle between the tangent line of the beam
            and the x-axis in radians at each mm of the beam.
        * etop: A numpy array containing the strain at the top of the
            cross-section at each mm of the beam.
        * ebot: A numpy array containing the strain at the bottom of the
            cross-section at each mm of the beam.
        * R: If 'supports' was provided, R is a 2-tuple of the reaction
            forces at said supports. Else R[0] is the reaction force at the
            clamped x=0 and R[1] is the reaction moment at that point.
        * length: Length in mm.
    """
    length, s1, s2 = _check_length_supports(length, supports)
    loads = _check_loads(loads)
    loads = [ld for ld in loads]  # make a copy since we modifiy it!
    EI, GA, top, bot = _check_arrays(length, EI, GA, top, bottom)
    if shear not in (True, False):
        raise ValueError("shear should be a boolean")
    # Calculate support loads.
    moment = sum([ld.moment(s1) for ld in loads])
    if s2:
        R2 = Load(force=-moment / (s2 - s1), pos=s2)
        loads.append(R2)
    else:  # clamped at x = 0
        R2 = -moment
    # Force equilibrium
    R1 = Load(force=-sum([ld.size for ld in loads]), pos=s1)
    loads.append(R1)
    # Calculate shear force
    D = np.sum(np.array([ld.shear(length) for ld in loads]), axis=0)
    # Calculate bending moment
    M = np.cumsum(D)
    Mstep = np.sum(
        np.array(
            [ld.moment_array(length) for ld in loads if isinstance(ld, MomentLoad)]
        ),
        axis=0,
    )
    M += Mstep
    if s2 is None:
        M -= M[-1]
    ddy_b = M / EI
    etop, ebot = -top * ddy_b, -bot * ddy_b
    dy = np.cumsum(ddy_b)
    if shear:
        dy += -1.5 * D / GA  # shear
    y = np.cumsum(dy)
    if s2:
        # First, translate the whole list so that the value at the
        # index anchor is zero.
        y = y - y[s1]
        # Then rotate around the anchor so that the deflection at the other
        # support is also 0.
        delta = -y[s2] / math.fabs(s1 - s2)
        slope = (
            np.concatenate((np.arange(-s1, 1, 1), np.arange(1, len(y) - s1))) * delta
        )
        dy += delta
        y = y + slope
    results = SimpleNamespace()
    results.length = length
    results.D, results.M = D, M
    results.dy, results.y, results.R = dy, y, (R1, R2)
    results.a = np.arctan(dy)
    results.etop, results.ebot = etop, ebot
    return results  # }}}


def save(results, path):  # {{{
    """
    Save the data from a solved results to a file as columns of numbers.
    It writes the following columns to the file:
    * position
    * shear force
    * bending moment
    * displacement
    * strain at top
    * strain at bottom
    * deflection angle

    Arguments:
        results: Results dictionary.
        path: Location where the data should be solved

    Raises:
        AttributeError if the results have not been solved yet.
    """
    data = np.vstack(
        (
            np.arange(results.length + 1),
            results.D,
            results.M,
            results.y,
            results.etop,
            results.ebot,
            results.dy,
        )
    ).T
    p = basename(path)
    d = str(datetime.now())[:-7]
    h = f"file: {p}\ngenerated: {d}\nx D M y et eb dy"
    np.savetxt(path, data, fmt="%g", header=h)  # }}}


def EI(sections, normal=None):  # {{{
    """Calculate the bending stiffnes of a cross-section.

    The cross-section is composed out of rectangular nonoverlapping sections
    that can have different Young's moduli.

    Each section is represented by a 4-tuple (width, height, offset, E).
    The offset is the distance from the top of the section to the top of the
    highest section. This should always be a positive value.
    E is the Young's modulus of the material of this section.

    Arguments:
        sections: Iterable of section properties.
        normal: The Young's modulus to which the total cross-section will be
            normalized. (Not used anymore, retained for compatibility.)

    Returns:
        Tuple of EI, top and bottom. Top and bottom are with respect to the
        neutral line.

    Examples:
        >>> E = 210000
        >>> B = 100
        >>> H = 20
        >>> sections = ((B, H, 0, E),)
        >>> EI(sections)
        (14000000000.0, 10.0, -10.0)

        >>> B = 100
        >>> h = 18
        >>> t = 1
        >>> H = h + 2 * t
        >>> E = 210000
        >>> sections = ((B, t, 0, E), (B, t, h+t, E))
        >>> EI(sections)
        (3794000000.0, 10.0, -10.0)

        >>> E1, E2 = 200000, 71000
        >>> t1, t2 = 1.5, 2.5
        >>> H = 31
        >>> B = 100
        >>> sections = ((B, t1, 0, E1), (B, t2, H-t2, E2))
        >>> EI(sections)
        (9393560891.143106, 11.530104712041885, -19.469895287958117)
    """
    normal = sections[0][-1]
    normalized = tuple((w * E / normal, h, offs) for w, h, offs, E in sections)
    A = sum(w * h for w, h, _ in normalized)
    S = sum(w * h * (offs + h / 2) for w, h, offs in normalized)
    yn = S / A
    # Find any geometry that straddles yn.
    to_split = tuple(g for g in sections if g[2] < yn and g[1] + g[2] > yn)
    geom = tuple(g for g in sections if g not in to_split)
    # split that geometry.
    # The new tuple has the format (width, height, top, bottom)
    new_geom = []
    for w, h, offs, E in to_split:
        h1 = yn - offs
        h2 = h - h1
        new_geom.append((w, h1, h1, 0, E))
        new_geom.append((w, h2, 0, -h2, E))
    # Convert the remaining geometry to reference yn.
    for w, h, offs, E in geom:
        new_geom.append((w, h, yn - offs, yn - offs - h, E))
    EI = sum(E * w * (top**3 - bot**3) / 3 for w, h, top, bot, E in new_geom)
    top = max(g[-3] for g in new_geom)
    bot = min(g[-2] for g in new_geom)
    return EI, top, bot  # }}}


def interpolate(tuples):  # {{{
    """
    Creates a numpy array and fills it by interpolation.

    Arguments:
        tuples: A list of 2-tuples (n, v). Note that the n values will be
            rounded and converted to integers.

    Returns:
        A numpy array with interpolated values so that at index n the array has
        the value v.

    Examples:
        >>> import numpy as np
        >>> interpolate([(0,0), (3,3)])
        array([0., 1., 2., 3.])
        >>> interpolate([(0,0), (4,3), (6,-1)])
        array([ 0.  ,  0.75,  1.5 ,  2.25,  3.  ,  1.  , -1.  ])
        >>> interpolate([(1,1), (4,4), (6,-3)])
        array([ 1. ,  2. ,  3. ,  4. ,  0.5, -3. ])
    """
    x = np.array([int(round(x)) for x, _ in tuples])
    y = np.array([y for _, y in tuples])
    startx, starty = x[0], y[0]
    arrays = []
    for dx, dy in zip(x[1:] - x[:-1], y[1:] - y[:-1]):
        if dx > 0:
            a = np.linspace(starty, starty + dy, num=dx + 1, endpoint=True)
            arrays.append(a[:-1])
        startx += dx
        starty += dy
    arrays.append(np.array([y[-1]]))
    return np.concatenate(arrays)  # }}}


def patientload(**kwargs):  # {{{
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
    f = _force(**kwargs)
    if "feet" in kwargs:
        s = round(float(kwargs["feet"]))
    elif "head" in kwargs:
        s = round(float(kwargs["head"])) - 1900
    else:
        raise ValueError("No 'feet' nor 'head' given.")
    fractions = [
        (0.148 * f, (s + 0, s + 450)),  # l. legs, 14.7% from 0--450 mm
        (0.222 * f, (s + 450, s + 1000)),  # upper legs
        (0.074 * f, (s + 1000, s + 1180)),  # hands
        (0.408 * f, (s + 1000, s + 1700)),  # torso
        (0.074 * f, (s + 1200, s + 1700)),  # arms
        (0.074 * f, (s + 1220, s + 1900)),
    ]  # head
    return [DistLoad(force=i[0], pos=i[1]) for i in fractions]  # }}}


class Load(object):  # {{{
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

        Examples:
            >>> str(Load(kg=150, pos=100))
            'point load of -1471.5 N @ 100 mm.'
        """
        self.size = _force(**kwargs)
        self.pos = round(float(kwargs["pos"]))

    def __str__(self):
        return f"point load of {self.size} N @ {self.pos} mm."

    def moment(self, pos):
        """
        Returns the bending moment that the load exerts at pos.
        """
        return (self.pos - pos) * self.size

    def shear(self, length):
        """
        Return the contribution of the load to the shear.

        Arguments:
            length: length of the array to return.

        Returns:
            An array that contains the contribution of this load.
        """
        rv = np.zeros(length + 1)
        rv[self.pos :] = self.size
        return rv  # }}}


class MomentLoad(Load):  # {{{
    def __init__(self, moment, pos):
        """Create a local bending moment load.

        Arguments:
            moment: bending moment in Nmm
            pos: position of the bending moment.
        """
        self.m = float(moment)
        Load.__init__(self, force=0, pos=pos)

    def __str__(self):
        return f"moment of {self.m} Nmm @ {self.pos}"

    def moment(self, pos):
        """
        Returns the bending moment that the load exerts at pos.
        """
        return self.m

    def shear(self, length):
        """
        Return the contribution of the load to the shear.

        Arguments:
            length: length of the array to return.

        Returns:
            An array that contains the contribution of this load.
        """
        return np.zeros(length + 1)

    def moment_array(self, length):
        """
        Return the contribution of the load to the bending moment.

        Arguments:
            length: length of the array to return.

        Returns:
            An array that contains the contribution of this load.
        """
        rv = np.zeros(length + 1)
        rv[self.pos :] = -self.m
        return rv  # }}}


class DistLoad(Load):  # {{{
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
        size = _force(**kwargs)
        self.start, self.end = _start_end(**kwargs)
        if self.start > self.end:
            self.start, self.end = self.end, self.start
        Load.__init__(self, force=size, pos=float(self.start + self.end) / 2)

    def __str__(self):
        return (
            f"constant distributed load of {self.size} N @ {self.start}--{self.end} mm."
        )

    def shear(self, length):
        rem = length + 1 - self.end
        d = self.end - self.start
        q = self.size
        parts = (np.zeros(self.start), np.linspace(0, q, d), np.ones(rem) * q)
        return np.concatenate(parts)  # }}}


class TriangleLoad(DistLoad):  # {{{
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
        self.pos = round(min(pos)) + 2.0 * length / 3.0
        self.q = 2 * self.size / length

    def __str__(self):
        if self.start < self.end:
            d = "ascending"
        else:
            d = "descending"
        return f"linearly {d} distributed load of {self.size} N @ {self.start}--{self.end} mm."

    def shear(self, length):
        rem = length + 1 - self.end
        parts = (
            np.zeros(self.start),
            np.linspace(0, self.q, self.end - self.start),
            np.ones(rem) * self.q,
        )
        dv = np.concatenate(parts)
        return np.cumsum(dv)  # }}}


# Everything below is internal to the module.


def _force(**kwargs):  # {{{
    """
    Determine the force. See Load.__init__()

    Returns:
        The force as a float.

    Examples:
        >>> _force(kg=1)
        -9.81
    """
    if "force" in kwargs:
        force = float(kwargs["force"])
    elif "kg" in kwargs:
        force = -9.81 * float(kwargs["kg"])
    else:
        raise KeyError("No 'force' or 'kg' present")
    return force  # }}}


def _start_end(**kwargs):  # {{{
    """
    Validate the position arguments. See DistLoad.__init_()

    Returns:
        Postition as a (start, end) tuple

    Examples:
        >>> _start_end(pos=(100, 200))
        (100, 200)
        >>> _start_end(start=100, end=200)
        (100, 200)
    """
    if "pos" in kwargs:
        p = kwargs["pos"]
        if not isinstance(p, tuple) and len(p) != 2:
            raise ValueError("'pos' should be a 2-tuple")
        pos = (round(float(kwargs["pos"][0])), round(float(kwargs["pos"][1])))
    elif "start" in kwargs and "end" in kwargs:
        pos = (round(float(kwargs["start"])), round(float(kwargs["end"])))
    else:
        raise KeyError("Neither 'pos' or 'start' and 'end' present")
    return pos  # }}}


def _check_length_supports(length, supports):  # {{{
    """
    Validate the length and supports. See solve().

    Returns:
        A tuple (length, support1, support2)
    """
    length = int(round(length))
    if length < 1:
        raise ValueError("length must be ≥1")
    if supports is not None:
        if len(supports) != 2:
            t = "The problem definition must contain exactly two supports."
            raise ValueError(t)
        s = (int(round(supports[0])), int(round(supports[1])))
        if s[0] == s[1]:
            raise ValueError("Two identical supports found!")
        elif s[0] > s[1]:
            s = (s[1], s[0])
        if s[0] < 0 or s[1] > length:
            raise ValueError("Support(s) outside of the beam!")
    else:
        s = (0, None)
    return (length, s[0], s[1])  # }}}


def _check_loads(loads):  # {{{
    """
    Validate the loads in the problem. See solve().

    Returns:
        A list of Loads
    """
    if isinstance(loads, Load):
        loads = [loads]
    if loads is None or len(loads) == 0:
        raise ValueError("No loads specified")
    for ld in loads:
        if not isinstance(ld, Load):
            raise ValueError("Loads must be Load instances")
    return list(loads)  # }}}


def _check_arrays(L, EI, GA, top, bottom):  # {{{
    """
    Validate the length of the EI, GA, top and bot iterables and converts
    them into numpy arrays. See solve().

    Returns:
        The modified EI, GA, top and bottom arrays.
    """
    rv = []
    for name, ar in zip(("EI", "GA", "top", "bottom"), (EI, GA, top, bottom)):
        # Convert single number to an ndarray.
        if isinstance(ar, (int, float)):
            ar = np.ones(L + 1) * ar
        # Convert list/tuple to ndarray.
        elif isinstance(ar, (list, tuple)):
            ar = np.array(ar)
        elif isinstance(ar, np.ndarray):
            pass
        else:
            raise ValueError(
                f"{name} is not a int, float, list, tuple or numpy.ndarray"
            )
        la = len(ar)
        if la != L + 1:
            raise ValueError(
                f"Length of {name} ({la}) doesn't match beam length ({L}) + 1 ."
            )
        rv.append(ar)
    return rv  # }}}
