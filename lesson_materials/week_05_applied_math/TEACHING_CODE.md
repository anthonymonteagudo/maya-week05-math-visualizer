# Week 5: code to present

These excerpts are generated from functions used by the actual visualizer. Import the package; do not run scene.py using desktop Python. Maya-specific excerpts require Maya. math_core.py works in ordinary Python.

## Suggested sequence

For a runnable, top-to-bottom numerical route, use [classroom_path.py](classroom_path.py). From the Tools folder: `python -m lesson_materials.week_05_applied_math.classroom_path`. It checks the same known values as the visualizer without creating or modifying a Maya scene. Work each equation on the board before running its numbered block.

Vectors → homogeneous coordinates → joint hierarchy → IK target/pole → orientation interpolation. Show one function at a time rather than the entire scene builder.

Beginner reading notes: a tuple holds ordered components; `zip(a, b)` pairs the matching components; `append` collects each answer. The matrix arrives from Maya as sixteen numbers in row order. `row * 4 + column` locates one entry. The explicit loops below intentionally show each multiply and accumulate step.

Read `math_core.py` first, then `rig.py`. `calculations.py` turns the live values into worked steps. `notation.py` and `presentation.py` arrange those steps on screen; they are UI support code, not prerequisites for the math exercise.

## Vector arithmetic

Show each function beside its equation. All inputs must share a coordinate space. unit returns None for a zero vector.

Live source: [math_core.py](./math_core.py) — `sub`.

```python
def sub(a, b):
    """Subtract corresponding components; end minus start is displacement."""
    result = []
    for component_a, component_b in zip(a, b):
        result.append(component_a - component_b)
    return tuple(result)
```

Live source: [math_core.py](./math_core.py) — `dot`.

```python
def dot(a, b):
    """Multiply corresponding components, then add the products."""
    total = 0.0
    for component_a, component_b in zip(a, b):
        total += component_a * component_b
    return total
```

Live source: [math_core.py](./math_core.py) — `cross`.

```python
def cross(a, b):
    """Return the perpendicular vector a cross b; order matters."""
    ax, ay, az = a
    bx, by, bz = b
    x = ay * bz - az * by
    y = az * bx - ax * bz
    z = ax * by - ay * bx
    return (x, y, z)
```

Live source: [math_core.py](./math_core.py) — `unit`.

```python
def unit(v):
    size = length(v)
    if size <= EPSILON:
        return None  # A zero vector has no direction.
    return scale(v, 1.0 / size)
```

## A point through a matrix

Contrast w=1 (point) with w=0 (direction). Maya uses row vectors; translation is the last row. A normal needs inverse-transpose treatment under nonuniform scale.

Live source: [math_core.py](./math_core.py) — `transform_homogeneous`.

```python
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
```

## Generate an arm hierarchy

Joint creation parents to the selected joint. Clear selection first; create shoulder, elbow, wrist in order; orient local X along the bones. Geometry is only a display proxy.

Live source: [rig.py](./rig.py) — `create_arm_chain`.

```python
def create_arm_chain(name, parent, positions):
    """Build shoulder -> elbow -> wrist; orient local X down each bone.

    name maps a short label into the caller's unique namespace.
    positions are three world-space points in Maya scene units.
    The caller owns the undo chunk and scene cleanup.
    """
    cmds.select(clear=True)
    joints = []
    for label, position in zip(("shoulder", "elbow", "wrist"), positions):
        joints.append(cmds.joint(name=name(label), position=position, radius=0.3))
    cmds.joint(joints[0], edit=True, orientJoint="xyz", secondaryAxisOrient="yup",
               children=True, zeroScaleOrient=True)
    cmds.joint(joints[-1], edit=True, orientJoint="none")
    cmds.parent(joints[0], parent)
    return joints
```

## Make the arm solve with IK

The IK target determines wrist position. The pole chooses the bend plane. These are different inputs to the same two-bone solve.

Live source: [rig.py](./rig.py) — `create_arm_ik`.

```python
def create_arm_ik(name, parent, joints, target, pole):
    """Target controls wrist position; pole chooses the two-bone bend plane."""
    handle, effector = cmds.ikHandle(name=name("arm_IK"), startJoint=joints[0],
                                   endEffector=joints[-1], solver="ikRPsolver")
    cmds.rename(effector, name("arm_effector"))
    cmds.parent(handle, parent)
    cmds.pointConstraint(target, handle, name=name("target_constraint"))
    cmds.poleVectorConstraint(pole, handle, name=name("pole_constraint"))
    cmds.setAttr(handle + ".ikBlend", 1)
    cmds.setAttr(handle + ".visibility", False)
    return handle
```

## Euler LERP versus quaternion SLERP

Compare the same endpoints at t=0.5. Euler angles represent an orientation; SLERP is an interpolation method. The comparison is Euler-component LERP versus quaternion SLERP.

Live source: [scene.py](./scene.py) — `interpolate`.

```python
    def interpolate(self, t, method="slerp"):
        """Compare fixed endpoints: identity to XYZ Euler (90, 90, 0) degrees."""
        if not 0 <= t <= 1:
            raise ValueError("t must be in [0,1].")
        if method not in ("slerp", "euler"):
            raise ValueError("Choose slerp or euler.")
        with edit_chunk("Week 5 interpolate"):
            if method == "slerp":
                q = om.MQuaternion.slerp(
                    om.MQuaternion(),
                    om.MEulerRotation(math.pi / 2, math.pi / 2, 0).asQuaternion(),
                    t,
                )
                # API rotation is radians; xform uses the current scene angular unit.
                rotation = q.asEulerRotation()
            else:
                rotation = om.MEulerRotation(t * math.pi / 2, t * math.pi / 2, 0)
            values = [om.MAngle(x).asUnits(om.MAngle.uiUnit()) for x in rotation]
            cmds.xform(self.hand, rotation=values, objectSpace=True)
            # Isolate orientation: translation would obscure the path comparison.
            cmds.setAttr(self.hand + ".translateX", 0)
```

## Small runnable math exercise

From the Tools directory, in Python (Maya is not needed):

```python
from lesson_materials.week_05_applied_math.math_core import transform_homogeneous

# Identity basis, with translation (10, 20, 30) in the last row.
world = (1,0,0,0, 0,1,0,0, 0,0,1,0, 10,20,30,1)
print(transform_homogeneous((3,4,0,1), world))  # (13,24,30,1)
print(transform_homogeneous((3,4,0,0), world))  # (3,4,0,0)
```

Ask: why does only the first result translate? Then rotate the parent in Maya and compare the displayed world coordinates.

## Code to keep behind the lesson

- `scene.py`: ownership, namespaces, reset, drawing arrows and labels, saved-scene DG connections.
- `ui.py`: Qt layout, callbacks, selection, polling and export coordination.
- `presentation.py` / `calculations.py`: display formatting and worked steps.
- `capture.py`: viewport export.

Those are useful tool-building examples later, but obscure the math when placed on a math slide. `lab_extension.py` remains an intentionally unfinished exercise, not a completed implementation.

## Scope of this cleanup

The joint hierarchy and IK setup now live in small functions in `rig.py`, called by `scene.build`. The matrix formatter now calls `math_core.transform_homogeneous` instead of embedding multiplication inside presentation code. The yellow marker mesh is removed; the matrix lesson samples the actual box corner (0.9, 0.175, 0.5). Older open Maya scenes retain their old geometry until rebuilt/reset with the updated module.
