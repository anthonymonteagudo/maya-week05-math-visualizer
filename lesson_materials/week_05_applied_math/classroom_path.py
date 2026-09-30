"""Read top to bottom with the Week 5 worked-example slides.

Run from the Tools folder:
    python -m lesson_materials.week_05_applied_math.classroom_path

Or in Maya: import this module and call main(). No scene is created or changed.
These are the same arithmetic functions used by the visualizer.
"""
from .math_core import add, sub, scale, length, unit, dot, cross, transform_homogeneous


def main():
    # 1. Positions -> displacements. E connects the arrows, not their midpoint.
    s = (0, 0, 0)
    e = (3, 4, 0)
    w = (6, 0, 0)
    a = sub(e, s)
    b = sub(w, e)
    print("1. Displacements:", a, b, "sum:", add(a, b))
    assert add(a, b) == sub(w, s)

    # 2. Separate direction from distance. Here a is known to be nonzero.
    direction = unit(a)
    speed = 2
    elapsed_time = 0.5
    movement = scale(direction, speed * elapsed_time)
    print("2. Length:", length(a), "unit direction:", direction, "movement:", movement)
    assert length(a) == 5
    assert abs(length(direction) - 1) < 1e-8

    # 3. A scalar answers an alignment question.
    forward = (1, 0, 0)
    print("3. Target ahead:", dot(forward, direction) > 0, "arm dot:", dot(a, b))
    assert dot(a, b) == -7

    # 4. Signed distance -> projected displacement -> point on the line.
    guide = sub(w, s)
    guide_direction = unit(guide)
    distance = dot(a, guide_direction)
    projected_offset = scale(guide_direction, distance)
    h = add(s, projected_offset)
    residual = sub(e, h)
    print("4. Projection H:", h, "residual:", residual)
    assert h == (3, 0, 0)
    assert dot(residual, guide_direction) == 0

    # 5. Cross gives a perpendicular vector; its magnitude is an area.
    perpendicular = cross(a, b)
    normal = unit(perpendicular)
    print("5. Cross:", perpendicular, "area:", length(perpendicular), "normal:", normal)
    assert perpendicular == (0, 0, -24)
    assert dot(normal, a) == dot(normal, b) == 0

    # 6. Maya row-vector convention: translation occupies the last row.
    matrix = (1, 0, 0, 0,
              0, 1, 0, 0,
              0, 0, 1, 0,
              10, 20, 30, 1)
    point = transform_homogeneous((3, 4, 0, 1), matrix)
    vector = transform_homogeneous((3, 4, 0, 0), matrix)
    print("6. Transformed point:", point, "direction:", vector)
    assert point == (13, 24, 30, 1)
    assert vector == (3, 4, 0, 0)

    # Extension: linear interpolation of position before orientation.
    start = (0, 0, 0)
    end = (4, 0, 0)
    t = 0.25
    position = add(scale(start, 1 - t), scale(end, t))
    print("7. Position LERP at t=0.25:", position)
    assert position == (1, 0, 0)


if __name__ == "__main__":
    main()
