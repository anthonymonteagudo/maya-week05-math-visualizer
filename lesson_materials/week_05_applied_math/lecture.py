"""Small, ordered scene recipes following the Week 5 refreshed slide deck.



Like Week 3's stage cards: select a step, load a variation, predict and check.

Only live-tool stops are listed; slide-only examples remain in the deck.

"""

BASE = ((0, 0, 0), (3, 4, 0), (6, 0, 0))





def vector(label, topic, points=BASE):

    return dict(label=label, topic=topic, points=points)





def pose(label, **values):

    return dict(label=label, **values)





def step(label, slides, mode, notice, *variations):

    return dict(label=label, slides=slides, mode=mode, notice=notice, variations=variations)





PROJECTION = (

    vector('Point off the guide', 'Dot / projection'),

    vector('Point on the guide: residual = 0', 'Dot / projection', ((0,0,0),(3,0,0),(6,0,0))),

    vector('No guide: W = S', 'Dot / projection', ((0,0,0),(3,4,0),(0,0,0))),

)



STEPS = (

    step('01 · One displacement', '23–29', 'vectors',

         'Move S or E. Predict a = E − S, then introduce length and unit direction.',

         vector('Start: S to E only', 'Step 1: S to E'),

         vector('Add length and unit direction', 'Normalize')),

    step('02 · Two connected movements', '30', 'vectors',

         'Move E while S and W stay fixed. Does a + b change?',

         vector('Two movements and their sum', 'Vectors')),

    step('03 · Direction and movement', '31–36', 'vectors',

         'Blue u is offset for comparison. Movement recipes show speed × time and the new position.',

         dict(vector('Worked movement: speed 2, time 0.5', 'Normalize'), movement=(2,.5)),

         dict(vector('Half the time: speed 2, time 0.25', 'Normalize'), movement=(2,.25)),

         vector('Unit direction (0.6, 0.8, 0)', 'Normalize'),

         dict(vector('Your turn: S=(1,1,0), E=(1,4,0)', 'Normalize', ((1,1,0),(1,4,0),(6,0,0))), movement=(4,.5)),

         vector('Reverse the displacement', 'Normalize', ((3,4,0),(0,0,0),(6,0,0))),

         vector('Zero displacement: E = S', 'Normalize', ((0,0,0),(0,0,0),(6,0,0)))),

    step('04 · Coordinate spaces', '39–53', 'rotations',

         'A space defines an origin, basis axes and units. Move the point or reference frame; compare the same point in two spaces.',

         pose('World: origin, axes and a point', space='world'),

         pose('Local to world: origin at (3,0,0)', space='local'),

         pose('Reference: rotate frame 90 Z', space='parent'),
         pose('Camera: C=(1,0,6), fixed world point', space='camera'),

         pose('Camera moved: C=(2,0,6), same point', space='camera_moved'),

         pose('Tangent: T, B and N on a surface', space='tangent'),


         pose('Point versus direction: translation', space='pointdir')),

    step('05 · Dot: alignment', '56–59, 63–66', 'vectors',

         'Predict the sign of the dot product before reading the scalar and angle.',

         vector('Connected vectors: dot = −7', 'Dot / alignment'),

         vector('Same direction', 'Dot / alignment', ((0,0,0),(3,4,0),(6,8,0))),

         vector('Right angle: dot = 0', 'Dot / alignment', ((0,0,0),(5,0,0),(5,5,0))),

         vector('Opposite directions', 'Dot / alignment', ((0,0,0),(3,4,0),(0,0,0)))),

    step('06 · Projection and residual', '60–62', 'vectors',

         'Locate H on the S–W line. Check that r = E − H is perpendicular to the guide.', *PROJECTION),

    step('07 · Cross: plane normal', '68–76', 'vectors',

         'Read the cross product before its unit normal. The normal arrow is drawn 3× for visibility.',

         vector('Bent pair: cross = (0,0,−24)', 'Cross / plane'),

         vector('Swap a and b: normal reverses', 'Cross / plane', ((0,0,0),(3,-4,0),(6,0,0))),

         vector('Parallel: no unique normal', 'Cross / plane', ((0,0,0),(3,4,0),(6,8,0)))),

    step('08 · Transforms and hierarchy', '78–88', 'rotations',

         'Change one transform. Track the yellow corner; its local coordinates are (0.9, 0.175, 0.5).',

         pose('Identity'), pose('Translation +3 X', translate=(3,0,0)),

         pose('Uniform scale ×2', scale=(2,2,2)), pose('Rotation +90° Z', rotate=(0,0,90)),

         pose('Parent rotation +90° Z', parent_rotate=(0,0,90))),

    step('09 · Orientations and rotation order', '89–93', 'rotations',

         'Compare the same two fixed-axis rotations in opposite orders. Gimbal lock and quaternion construction use the slides.',

         pose('Start: identity'), pose('End: Euler (90,90,0)', rotate=(90,90,0)),

         pose('Fixed axes: X then Y', order='xy'), pose('Fixed axes: Y then X', order='yx')),

    step('10 · Position interpolation', '94', 'rotations',

         'Use t to move the object origin from local X=0 to X=4. Predict the halfway position.',

         pose('Start: t = 0', view=2, t=0), pose('Halfway: t = 0.5', view=2, t=.5),

         pose('End: t = 1', view=2, t=1)),

    step('11 · Orientation interpolation', '95–96', 'rotations',

         'Compare Euler LERP and quaternion SLERP at the same t. The reference boxes show the endpoints.',

         pose('Euler LERP: halfway', view=1, method=1, t=.5),

         pose('Quaternion SLERP: halfway', view=1, method=0, t=.5),

         pose('Start: t = 0', view=1, method=0, t=0), pose('End: t = 1', view=1, method=0, t=1)),

    step('12 · Guided projection exercise', '97–101', 'vectors',

         'Open lab_extension.py. Recreate H, then check the known case and both edge cases.', *PROJECTION),

    step('13 · Week 6 preview (optional)', '104', 'arm',

         'A brief application preview. Rig construction, FK/IK, and constraints receive their deeper treatment next week.',

         pose('Arm: IK and the bend plane')),

)





def apply(demo, variation):

    """Restore this recipe inside the selected lesson, without rebuilding a scene."""

    from maya import cmds

    from maya.api import OpenMaya as om

    import math

    from . import spaces

    spaces.clear(demo)

    demo.movement = variation.get('movement')

    if demo.mode == 'arm':

        demo.display('Rig only')

        return

    for node in (demo.root, demo.rotation_parent, demo.hand):

        for attr, value in (('translate',(0,0,0)), ('rotate',(0,0,0)), ('scale',(1,1,1))):

            cmds.setAttr(node+'.'+attr, *value)

    if demo.mode == 'vectors':

        for node, point in zip(demo.points, variation['points']):

            cmds.setAttr(node+'.translate', *point)

        demo.display(variation['topic'])

    else:

        demo.display('Vectors')

        if variation.get('space'):

            spaces.prepare(demo, variation['space'])

            return

        for attr in ('translate', 'rotate', 'scale'):

            if attr in variation:

                cmds.setAttr(demo.hand+'.'+attr, *variation[attr])

        if 'parent_rotate' in variation:

            cmds.setAttr(demo.rotation_parent+'.rotate', *variation['parent_rotate'])

        if 'order' in variation:

            rx = om.MEulerRotation(math.pi/2,0,0).asMatrix()

            ry = om.MEulerRotation(0,math.pi/2,0).asMatrix()

            result = om.MTransformationMatrix(rx*ry if variation['order']=='xy' else ry*rx).rotation()

            cmds.setAttr(demo.hand+'.rotate', *(math.degrees(x) for x in result))

        if variation.get('view') == 1:

            demo.interpolate(variation.get('t',0), 'euler' if variation.get('method') else 'slerp')

        elif variation.get('view') == 2:

            cmds.setAttr(demo.hand+'.translateX', 4*variation.get('t',0))

        for name in ('start_pose','end_pose','rotation_labels'):

            cmds.setAttr(demo.name(name)+'.visibility', variation.get('view') == 1)
