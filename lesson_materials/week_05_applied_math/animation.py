"""Sample orientations into a separate, reusable Maya animation take."""
import math
from maya import cmds
from maya.api import OpenMaya as om


def rotation_at(t, method):
    end=om.MEulerRotation(math.pi/2,math.pi/2,0)
    rotation=(om.MQuaternion.slerp(om.MQuaternion(),end.asQuaternion(),t).asEulerRotation()
              if method=="slerp" else om.MEulerRotation(t*math.pi/2,t*math.pi/2,0))
    return [om.MAngle(x).asUnits(om.MAngle.uiUnit()) for x in rotation]


def bake_comparison(start=1, frames=96):
    """Create two independent keyed boxes. Never key or overwrite the lesson controls.

    Linear Euler samples approximate SLERP between frames; integer-frame samples
    are exact. Duration is frames/current scene FPS. Playback range is not changed.
    """
    if frames<2: raise ValueError("At least two frames are required.")
    selection=cmds.ls(selection=True,long=True) or []
    cmds.undoInfo(openChunk=True,chunkName="Bake Week 5 comparison")
    try:
        group=cmds.group(empty=True,name="Week05_BakedComparison#")
        for method,x in (("euler",-1.5),("slerp",1.5)):
            box=cmds.polyCube(name=method+"_take#",width=1.8,height=.35,depth=1,constructionHistory=False)[0]
            cmds.parent(box,group)
            cmds.setAttr(box+".translateX",x)
            for index in range(frames+1):
                for axis,value in zip("XYZ",rotation_at(index/frames,method)):
                    cmds.setKeyframe(box,attribute="rotate"+axis,time=start+index,value=value,inTangentType="linear",outTangentType="linear")
        cmds.addAttr(group,longName="takeStart",attributeType="long",defaultValue=start)
        cmds.addAttr(group,longName="takeEnd",attributeType="long",defaultValue=start+frames)
        return group
    finally:
        cmds.undoInfo(closeChunk=True)
        cmds.select(selection,replace=True)
