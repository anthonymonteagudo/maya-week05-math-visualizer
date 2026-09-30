"""Worked calculations from the same world-space samples used by the visualizer.

Formatting rounds only for display. Calculation never uses rounded values.
This module is Maya-independent so known answers can be tested outside the UI.
"""
import math
from .math_core import add, sub, dot, length, unit, transform_homogeneous


def number(value):
    return "{:.4f}".format(0 if abs(value) < 0.00005 else value).rstrip("0").rstrip(".")


def vector(value):
    return "(" + ", ".join(number(x) for x in value) + ")"


def products(a, b):
    return " + ".join("({} * {})".format(number(x), number(y)) for x, y in zip(a, b))


def vectors(data, topic, target=None):
    s, e, w = data["points"]
    a, b = data["upper"], data["lower"]
    lines = ["LIVE INPUTS | world space | " + data["units"],
             "S = " + vector(s), "E = " + vector(e), "W = " + vector(w),
             "a = E - S (teal); b = W - E (gold)", ""]
    if topic in ("Step 1: S to E", "Normalize"):
        lines = ["LIVE INPUTS | world space | " + data["units"],
                 "S = " + vector(s), "E = " + vector(e), "a = E - S (teal)", ""]
    if topic == "Step 1: S to E":
        lines += ["SUBTRACTION -> displacement", "a = E - S",
                  "  = " + vector(e) + " - " + vector(s),
                  "  = (" + ", ".join("{} - ({})".format(number(x), number(y)) for x,y in zip(e,s)) + ")",
                  "  = " + vector(a),
                  "APPLICATION: move from start S to end E."]
    elif topic == "Vectors":
        lines += ["SUBTRACTION -> displacement", "a = E - S",
                  "  = " + vector(e) + " - " + vector(s),
                  "  = (" + ", ".join("{} - ({})".format(number(x), number(y)) for x,y in zip(e,s)) + ")",
                  "  = " + vector(a), "b = W - E = " + vector(b), "",
                  "ADDITION -> total displacement", "a + b = (E - S) + (W - E) = W - S",
                  vector(a) + " + " + vector(b) + " = " + vector(add(a,b)),
                  "APPLICATION: chain shoulder-to-elbow and elbow-to-wrist offsets.",
                  "Teal and gold are placed head-to-tail. The green S-to-W arrow is their sum."]
    elif topic == "Normalize":
        size = data["upper_length"]
        lines += ["MAGNITUDE -> length", "|a| = sqrt(ax^2 + ay^2 + az^2)",
                  "    = sqrt(" + " + ".join("({})^2".format(number(x)) for x in a) + ")",
                  "    = sqrt({}) = {} {}".format(number(dot(a,a)), number(size), data["units"]),
                  "", "NORMALIZATION -> direction without distance", "u = a / |a|"]
        if data["upper_unit"] is None:
            lines += ["UNDEFINED: |a| = 0, so division by its length is not valid.",
                      "No blue unit arrow is drawn."]
        else:
            lines += ["  = {} / {} = {}".format(vector(a),number(size),vector(data["upper_unit"])),
                      "|u| = 1 (dimensionless)",
                      "APPLICATION: direction for an aim or movement command.",
                      "Blue has the teal arrow's direction, with length one."]
    elif topic in ("Dot / alignment", "Dot / projection"):
        lines += ["DOT -> signed alignment", "a dot b = ax*bx + ay*by + az*bz",
                  "        = " + products(a,b), "        = " + number(data["dot"]),
                  "cos(theta) = (a dot b) / (|a| |b|)"]
        if data["cosine"] is None:
            lines += ["UNDEFINED angle: at least one input vector has zero length."]
        else:
            lines += [" = {} / ({} * {}) = {}".format(number(data["dot"]),number(data["upper_length"]),number(data["lower_length"]),number(data["cosine"])),
                      "theta = acos(clamp(cos(theta), -1, 1)) = {} degrees".format(number(data["angle"])),
                      "Interior elbow angle = 180 - theta = {} degrees".format(number(180-data["angle"]))]
            lines += ["Numerical guard: inverse cosine uses a cosine clamped to [-1, 1] to guard floating-point roundoff."]
        if topic == "Dot / alignment":
            return "\n".join(lines)
        g = sub(w,s)
        u = unit(g)
        lines += ["", "PROJECTION -> closest point H on the S-W line", "g (guide from S to W) = W - S = " + vector(g), "u = g / |g|"]
        if u is None:
            lines += ["UNDEFINED: S = W, so this line has no direction.", "No projection arrow is drawn."]
        else:
            distance = dot(a,u)
            lines += ["u = " + vector(u), "k = a dot u = " + products(a,u) + " = " + number(distance),
                      "p = k*u = " + vector(sub(data["projection"], s)),
                      "H = S + p = {} + {}".format(vector(s),vector(sub(data["projection"], s))),
                      "H = " + vector(data["projection"]), "r = E - H = " + vector(data["bend"]),
                      "APPLICATION: find the elbow's offset from the shoulder-wrist line.",
                      "Purple ends at H; pink connects H to E. This is an infinite-line projection."]
    elif topic == "Cross / plane":
        lines += ["CROSS -> perpendicular vector", "a x b = (ay*bz - az*by, az*bx - ax*bz, ax*by - ay*bx)"]
        for label, i, j in [("x",1,2),("y",2,0),("z",0,1)]:
            lines.append("c{} = a{}*b{} - a{}*b{}".format(label,"xyz"[i],"xyz"[j],"xyz"[j],"xyz"[i]))
            lines.append("c{} = {}*{} - {}*{} = {}".format(label,number(a[i]),number(b[j]),number(a[j]),number(b[i]),number(data["cross"]["xyz".index(label)])))
        lines += ["a x b = " + vector(data["cross"]),
                  "|a x b| = parallelogram area = " + number(length(data["cross"])) + " " + data["units"] + "^2",
                  "n = (a x b) / |a x b|"]
        if data["normal"] is None:
            lines += ["UNDEFINED normal: inputs are zero or effectively parallel. No red normal is drawn."]
        else:
            lines += ["n = " + vector(data["normal"])]
        lines += ["APPLICATION: orient a rig's bend plane or construct a surface basis.",
                  "Reversing input order flips the normal. A normal is not a pole-control position."]
    else:
        reach = data["upper_length"] + data["lower_length"]
        lines += ["ARM REACH -> distance constraint", "L1 = |E - S| = " + number(data["upper_length"]),
                  "L2 = |W - E| = " + number(data["lower_length"]),
                  "Maximum reach = L1 + L2 = " + number(reach)]
        if target is not None:
            distance = length(sub(target,s))
            lines += ["Target T = " + vector(target), "r = |T - S| = |" + vector(sub(target,s)) + "| = " + number(distance),
                      "Reachable distance: |L1-L2| <= r <= L1+L2",
                      "{} <= {} <= {}".format(number(abs(data["upper_length"]-data["lower_length"])),number(distance),number(reach)),
                      "Distance condition: " + ("REACHABLE" if abs(data["upper_length"]-data["lower_length"]) - 1e-8 <= distance <= reach + 1e-8 else "OUTSIDE REACH"),
                      "APPLICATION: IK aims for T while keeping both bone lengths fixed.",
                      "This distance check explains reach; Maya's IK solver also uses the pole to choose the bend plane."]
    lines += ["", "Displayed values are rounded to 4 decimal places; calculations use full precision."]
    return "\n".join(lines)


def matrix(values, point=(0.9,0.175,0.5), description="This point is the box corner (+X, +Y, +Z) in local space."):
    p = tuple(point) + (1,)
    out = transform_homogeneous(p, values)
    lines = ["LOCAL POINT -> WORLD POINT", "Maya convention: row vectors, translation in the last row.",
             "p_world = p_local * M_world", "p_local = " + vector(p),
             description, "M_world ="]
    lines += ["  " + vector(values[i:i+4]) for i in range(0,16,4)]
    lines += ["Maya convention: each output component uses one matrix column.",
              "x_world = x_local*m00 + y_local*m10 + z_local*m20 + w_local*m30",
              "y_world = x_local*m01 + y_local*m11 + z_local*m21 + w_local*m31",
              "z_world = x_local*m02 + y_local*m12 + z_local*m22 + w_local*m32",
              "w_world = x_local*m03 + y_local*m13 + z_local*m23 + w_local*m33"]
    for j,label in enumerate("xyzw"):
        lines.append(label + " = " + products(p,[values[i*4+j] for i in range(4)]) + " = " + number(out[j]))
    lines += ["p_world = " + vector(out), "APPLICATION: carry a local attachment point through a parent hierarchy.",
              "A point has homogeneous w=1; a direction uses w=0, so translation does not affect it."]
    direction=tuple(point)+(0,)
    mapped_direction=transform_homogeneous(direction,values)
    lines += ["", "DIRECTION -> same components, w=0", "v_local = "+vector(direction),
              "v_world = v_local * M_world = "+vector(mapped_direction),
              "Translation contributes zero because the direction has w=0."]
    return "\n".join(lines)


def interpolation(t, method):
    lines = ["SYMBOLS -> orientation", "t = progress from 0 (start) to 1 (end)", "q = unit quaternion representing an orientation; q0=start, q1=end", "q=(x,y,z,w): xyz = axis*sin(angle/2); w = cos(angle/2)", "Quaternion w is not the W point and is not homogeneous-coordinate w.", "omega = angle between q0 and q1 in quaternion space (half the physical rotation angle)", "ORIENTATION INTERPOLATION | t = " + number(t),
             "Start XYZ = (0, 0, 0); end XYZ = (90, 90, 0) degrees."]
    if method == "euler":
        lines += ["e(t) = (1-t)*e0 + t*e1", "     = (1-{})*(0,0,0) + {}*(90,90,0)".format(number(t),number(t)),
                  "     = " + vector((90*t,90*t,0)) + " degrees", "XYZ rotation order converts these angles into the visible orientation."]
    else:
        # Maya XYZ endpoint quaternion, explicitly in x,y,z,w order.
        q0, q1 = (0,0,0,1), (0.5,0.5,-0.5,0.5)
        omega = math.acos(0.5)
        a, b = math.sin((1-t)*omega)/math.sin(omega), math.sin(t*omega)/math.sin(omega)
        lines += ["q = (x, y, z, w)", "q0 = " + vector(q0), "q1 = " + vector(q1),
                  "omega = acos(q0 dot q1) = acos(0.5) = 60 degrees",
                  "q(t) = sin((1-t)*omega)/sin(omega) * q0 + sin(t*omega)/sin(omega) * q1",
                  "     = {} * q0 + {} * q1".format(number(a),number(b)),
                  "     = " + vector(tuple(a*x+b*y for x,y in zip(q0,q1))),
                  "Quaternion arc angle is 60 degrees; the physical endpoint rotation is 120 degrees."]
    lines += ["APPLICATION: interpolate an object's orientation between poses.",
              "Compare t=0.5: same endpoints, different intermediate orientations.",
              "This is the slider calculation. Manually rotating the proxy overrides that pose until the slider is used again."]
    return "\n".join(lines)


def movement(data, speed, elapsed):
    s, e, _ = data["points"]
    direction = data["upper_unit"]
    lines = ["MOVEMENT | world space | " + data["units"],
             "S = " + vector(s), "E = " + vector(e),
             "a = E - S = " + vector(data["upper"]),
             "|a| = " + number(data["upper_length"]) + " " + data["units"]]
    if direction is None:
        return "\n".join(lines + ["UNDEFINED direction: E = S. Do not normalize the zero vector."])
    travel = speed * elapsed
    displacement = tuple(x * travel for x in direction)
    lines += ["u = a / |a| = " + vector(direction),
              "Speed = " + number(speed) + " " + data["units"] + "/s",
              "Elapsed time = " + number(elapsed) + " s",
              "Travel distance = speed * time = " + number(travel) + " " + data["units"],
              "Movement = u * travel distance = " + vector(displacement),
              "New position = S + movement = " + vector(add(s, displacement)),
              "E defines the direction. This is constant-speed movement; it does not clamp at E."]
    return "\n".join(lines)
