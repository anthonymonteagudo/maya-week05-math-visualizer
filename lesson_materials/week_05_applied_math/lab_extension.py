"""Guided student extension. Complete only the projection calculation.

Drawing and scene acquisition are supplied. Do not implement a production IK solver.
"""
from .math_core import add, dot, scale, sub, unit  # noqa: F401 -- supplied lab vocabulary


def elbow_projection(shoulder, elbow, wrist):
    """Return the projection H, or None when shoulder and wrist coincide.

    Known answer: (0,0,0), (3,4,0), (6,0,0) -> (3,0,0).
    Implement using the imported vector helpers, then test translation invariance.
    """
    raise NotImplementedError("Find the unit guide, then project E-S onto it and add S.")
