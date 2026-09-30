"""Resizable, screen-facing lesson labels for Maya Viewport 2.0.

Local teaching plug-in: the development type ID is not a published product ID.
"""
from maya.api import OpenMaya as om, OpenMayaUI as omui, OpenMayaRender as omr

def maya_useNewAPI():
    pass

TYPE_NAME = 'week05TeachingLabel'
TYPE_ID = om.MTypeId(0x0007F505)
CLASSIFICATION = 'drawdb/geometry/week05TeachingLabel'
REGISTRANT = 'Week05TeachingLabelDraw'


class LabelNode(omui.MPxLocatorNode):
    @staticmethod
    def creator():
        return LabelNode()

    @staticmethod
    def initialize():
        typed = om.MFnTypedAttribute()
        LabelNode.text = typed.create('labelText', 'lt', om.MFnData.kString)
        LabelNode.addAttribute(LabelNode.text)
        numeric = om.MFnNumericAttribute()
        LabelNode.size = numeric.create('fontSize', 'fs', om.MFnNumericData.kInt, 24)
        numeric.setMin(8); numeric.setMax(240)
        LabelNode.addAttribute(LabelNode.size)
        LabelNode.color = numeric.createColor('labelColor', 'lc')
        numeric.default = (1.0, 1.0, 1.0)
        LabelNode.addAttribute(LabelNode.color)


class LabelData(om.MUserData):
    def __init__(self):
        super().__init__(False)


class LabelDraw(omr.MPxDrawOverride):
    def __init__(self, obj):
        super().__init__(obj, None, True)

    @staticmethod
    def creator(obj):
        return LabelDraw(obj)

    def supportedDrawAPIs(self):
        return omr.MRenderer.kAllDevices

    def isBounded(self, obj_path, camera_path):
        return False

    def hasUIDrawables(self):
        return True

    def prepareForDraw(self, obj_path, camera_path, frame_context, old_data):
        data = old_data if isinstance(old_data, LabelData) else LabelData()
        node = om.MFnDependencyNode(obj_path.node())
        data.text = node.findPlug('labelText', False).asString()
        data.size = node.findPlug('fontSize', False).asInt()
        color = node.findPlug('labelColor', False)
        data.color = om.MColor(tuple(color.child(i).asFloat() for i in range(3)))
        return data

    def addUIDrawables(self, obj_path, manager, frame_context, data):
        manager.beginDrawable()
        manager.setColor(data.color)
        manager.setFontName('Arial')
        manager.setFontSize(data.size)
        manager.setFontWeight(omr.MUIDrawManager.kWeightBold)
        manager.text(om.MPoint(0,0,0), data.text, omr.MUIDrawManager.kCenter)
        manager.endDrawable()


def initializePlugin(obj):
    plugin = om.MFnPlugin(obj, 'Week 5 teaching tools', '1.0', 'Any')
    plugin.registerNode(TYPE_NAME, TYPE_ID, LabelNode.creator, LabelNode.initialize,
                        om.MPxNode.kLocatorNode, CLASSIFICATION)
    omr.MDrawRegistry.registerDrawOverrideCreator(CLASSIFICATION, REGISTRANT, LabelDraw.creator)


def uninitializePlugin(obj):
    omr.MDrawRegistry.deregisterDrawOverrideCreator(CLASSIFICATION, REGISTRANT)
    om.MFnPlugin(obj).deregisterNode(TYPE_ID)
