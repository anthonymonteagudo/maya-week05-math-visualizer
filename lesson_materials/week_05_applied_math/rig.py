"""Small Maya rig operations used by the live lesson (suitable for code walkthroughs)."""
from maya import cmds


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
