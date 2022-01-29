.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

Introduction
============

Over the years I've written several programs in languages from Perl to Lua to
solve the differential equations for pure bending d²y/dx² = M/(E·I) and shear
dy/dx = α·V/(G·A) of beams.  These equations are used to study the deformation
and stresses in structures.

For the simple cases of pure bending under a single load (where E·I is
constant over the length of the beam, and where shear deformation is ignored),
solutions can be found in reference books.  Combining them for different loads
can be rather cumbersome,though.

However, in practice I usually deal with cases where the bending stiffness E·I
(and shear stiffness G·A) vary along the length of the beam, where there may
be multiple loads present and where shear deflection cannot be ignored.
Therefore I began to calculate my own solutions.  These programs all followed
the same pattern.  The solution is determined by discretization and
integration.  So I decided to separate the re-usable parts and put them in a
module.  That was the birth of beammech.py.

Using beammech.py
=================

Currently, this module is being developed and tested in Python 3.6+ only.

This software uses *metric units* throughout.  Mass is in kg, forces are in N,
and lengths in mm.  The accelleration of gravity is set at 9.81 m/s².  A
standard Cartesian coordinate system is used, with the x-axis pointing to the
right from 0 and the y-axis pointing up.  The length of each segment dx for
summation (integration) is 1 mm, because that is a good match for the kind of
problems I use it for.  And it makes the math simpler; A whole lot of
divisions just disappear.

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
