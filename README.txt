INTRODUCTION

Over the years I've written several programs in languages from Perl to Lua to
solve the differential equations for pure bending [y'' = M/(E·I)] and shear
[y' = α·V/(G·A)] of beams.

For the simple cases of pure bending (where E·I is constant over the length of
the beam, and where shear deformation is ignored), the solution can be found
in reference books.

However, in practice I usually deal with cases where E·I (and G·A) vary along
the length of the beam, and where shear deflection cannot be ignored. So I had
to calculate my own solutions.

These programs all followed the same pattern. So I decided to separate the
re-usable parts and put them in a module. That was the birth of beammech.py.


USING BEAMMECH.PY

The first task is to define a function that gives the cross-section properties
along the length of the beam. It takes a single integer argument indicating
the position along the beam, and should return a four-tuple containing the
second area moment (I), shear stiffness (G·A) and the distances from the
neutral line to the top and bottom of the beam respectively.

The next task is to create a tuple containing the positions of the two simple
supports of the beam. Then a list of loads (objects that inherit from the Load
class). These two, along with the length of the beam, are used as arguments to
the beammech.shearforce function. This returns a list of the shear force at
every millimeter along the length of the beam.

This list of shear forces, along with the Young's Modulus of the beam's
material and the function for producing the cross-sectional properties and the
supports are used as input to the beammech.loadcase function. This returns a
tuple of four lists; the bendinb moment in the cross-section, the deflection
of the beam and the stress at the top and bottom of the beam. These form the
solution of the load case.

