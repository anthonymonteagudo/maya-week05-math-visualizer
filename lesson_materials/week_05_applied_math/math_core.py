"""Small, Maya-independent calculations used by the readouts and guided lab.

Points must use the same space and length unit. Angles returned here are degrees.
"""

import math

EPSILON = 1e-8
PRESETS = {
    "Bent arm": ((0.0, 0.0, 0.0), (3.0, 4.0, 0.0), (6.0, 0.0, 0.0)),
    "Perpendicular": ((0.0, 0.0, 0.0), (5.0, 0.0, 0.0), (5.0, 5.0, 0.0)),
    "Straight": ((0.0, 0.0, 0.0), (5.0, 0.0, 0.0), (10.0, 0.0, 0.0)),
    "Coincident shoulder/wrist": ((0.0, 0.0, 0.0), (3.0, 4.0, 0.0), (0.0, 0.0, 0.0)),
    "Zero upper segment": ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (6.0, 0.0, 0.0)),
}


def add(a, b):
    """Add corresponding components, in the same coordinate space."""
    result = []
    for component_a, component_b in zip(a, b):
        result.append(component_a + component_b)
    return tuple(result)


def sub(a, b):
    """Subtract corresponding components; end minus start is displacement."""
    result = []
    for component_a, component_b in zip(a, b):
        result.append(component_a - component_b)
    return tuple(result)


def scale(v, s):
    """Multiply every component by the same scalar."""
    result = []
    for component in v:
        result.append(component * s)
    return tuple(result)


def dot(a, b):
    """Multiply corresponding components, then add the products."""
    total = 0.0
    for component_a, component_b in zip(a, b):
        total += component_a * component_b
    return total


def length(v):
    return math.sqrt(dot(v, v))


def cross(a, b):
    """Return the perpendicular vector a cross b; order matters."""
    ax, ay, az = a
    bx, by, bz = b
    x = ay * bz - az * by
    y = az * bx - ax * bz
    z = ax * by - ay * bx
    return (x, y, z)


def unit(v):
    size = length(v)
    if size <= EPSILON:
        return None  # A zero vector has no direction.
    return scale(v, 1.0 / size)


def analyze(shoulder, elbow, wrist):
    """Return explicit None for undefined directions, angles and projections."""
    for p in (shoulder, elbow, wrist):
        if len(p) != 3 or not all(math.isfinite(x) for x in p):
            raise ValueError("Expected three finite components per point.")
    a, b = sub(elbow, shoulder), sub(wrist, elbow)
    ua, ub, guide = unit(a), unit(b), unit(sub(wrist, shoulder))
    cosine = max(-1.0, min(1.0, dot(ua, ub))) if ua and ub else None
    normal = cross(a, b)
    # Relative collinearity guard: independent of segment lengths.
    plane_valid = bool(ua and ub and length(cross(ua, ub)) > EPSILON)
    h = None
    if guide is not None:
        distance_along_line = dot(a, guide)
        projected_offset = scale(guide, distance_along_line)
        h = add(shoulder, projected_offset)
    bend = sub(elbow, h) if h is not None else None
    direction = unit(bend) if bend is not None else None
    return dict(
        upper=a,
        lower=b,
        upper_length=length(a),
        lower_length=length(b),
        upper_unit=ua,
        dot=dot(a, b),
        cosine=cosine,
        angle=math.degrees(math.acos(cosine)) if cosine is not None else None,
        cross=normal,
        normal=unit(normal) if plane_valid else None,
        projection=h,
        bend=bend,
        helper=add(elbow, scale(direction, 2.0)) if direction else None,
    )


def transform_homogeneous(vector4, matrix16):
    """Multiply a row vector by a row-major 4x4 matrix, as Maya does.

    Use (x, y, z, 1) for a point; (x, y, z, 0) for a direction.
    A direction ignores translation. Normals need separate treatment under
    nonuniform scale. This returns homogeneous coordinates without division.
    """
    if len(vector4) != 4 or len(matrix16) != 16:
        raise ValueError("Expected four vector components and sixteen matrix entries.")
    result = []
    for column in range(4):
        # Each output component is the row vector dotted with one column.
        component = 0.0
        for row in range(4):
            matrix_entry = matrix16[row * 4 + column]
            component += vector4[row] * matrix_entry
        result.append(component)
    return tuple(result)
