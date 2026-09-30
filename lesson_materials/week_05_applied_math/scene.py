"""Generated Maya fixtures. Native DG nodes drive all vector/projection geometry.



Each build owns a unique namespace. Never reset, rename, or delete another scene.

UI/readout code is optional: the saved geometry works without Python callbacks.

"""



import math

import json

from contextlib import contextmanager



from maya import cmds

from maya.api import OpenMaya as om



from .math_core import PRESETS, analyze

from .rig import create_arm_chain, create_arm_ik





@contextmanager

def edit_chunk(label):

    selection = cmds.ls(selection=True, long=True) or []

    cmds.undoInfo(openChunk=True, chunkName=label)

    try:

        yield

    finally:

        cmds.select([x for x in selection if cmds.objExists(x)], replace=True)

        cmds.undoInfo(closeChunk=True)





class Demo:

    def __init__(self, namespace, mode):

        self.namespace, self.mode = namespace, mode

        self.nodes = []

        self.points = []

        self.topic = "Vectors"

        self.root = self.name("DEMO")



    def name(self, name):

        return self.namespace + ":" + name



    def node(self, kind, name):

        n = cmds.createNode(kind, name=self.name(name))

        self.nodes.append(n)

        return n



    def plug(self, value, target):

        if isinstance(value, str):

            cmds.connectAttr(value, target, force=True)

        elif isinstance(value, (tuple, list)):

            cmds.setAttr(target, *value, type="double3")

        else:

            cmds.setAttr(target, value)



    def vector(self, name, a, b, operation=1):

        n = self.node("plusMinusAverage", name)

        cmds.setAttr(n + ".operation", operation)

        self.plug(a, n + ".input3D[0]")

        self.plug(b, n + ".input3D[1]")

        return n + ".output3D"



    def product(self, name, a, b=None, operation=0, normalize=False):

        if normalize:

            # Never feed a zero vector to Maya's normalizer (including during reset).

            valid = self.valid(name + "_valid", self.magnitude(name + "_length", a))

            safe = self.node("condition", name + "_safe_input")

            self.plug(valid, safe + ".firstTerm")

            cmds.setAttr(safe + ".secondTerm", 1)

            self.plug(a, safe + ".colorIfTrue")

            cmds.setAttr(safe + ".colorIfFalse", 1, 0, 0, type="double3")

            a = safe + ".outColor"

        n = self.node("vectorProduct", name)

        cmds.setAttr(n + ".operation", operation)

        cmds.setAttr(n + ".normalizeOutput", normalize)

        self.plug(a, n + ".input1")

        if b is not None:

            self.plug(b, n + ".input2")

        if normalize:

            output = self.node("condition", name + "_guarded")

            self.plug(valid, output + ".firstTerm")

            cmds.setAttr(output + ".secondTerm", 1)

            self.plug(n + ".output", output + ".colorIfTrue")

            cmds.setAttr(output + ".colorIfFalse", 0, 0, 0, type="double3")

            return output + ".outColor"

        return n + ".output"



    def magnitude(self, name, vector):

        n = self.node("distanceBetween", name)

        self.plug(vector, n + ".point2")

        return n + ".distance"



    def valid(self, name, value, threshold=1e-8):

        n = self.node("condition", name)

        self.plug(value, n + ".firstTerm")

        cmds.setAttr(n + ".secondTerm", threshold)

        cmds.setAttr(n + ".operation", 2)  # Greater than.

        cmds.setAttr(n + ".colorIfTrueR", 1)

        cmds.setAttr(n + ".colorIfFalseR", 0)

        return n + ".outColorR"



    def world(self, node, label):

        n = self.node("decomposeMatrix", label + "_world")

        cmds.connectAttr(node + ".worldMatrix[0]", n + ".inputMatrix")

        return n + ".outputTranslate"



    def color(self, node, rgb):

        cmds.setAttr(node + ".overrideEnabled", True)

        cmds.setAttr(node + ".overrideRGBColors", True)

        cmds.setAttr(node + ".overrideColorRGB", *rgb)

        shapes = cmds.listRelatives(node, shapes=True, fullPath=True) or []

        if any(cmds.nodeType(s) == "mesh" for s in shapes):

            shader = cmds.shadingNode("surfaceShader", asShader=True, name=self.name("color"))

            cmds.setAttr(shader + ".outColor", *rgb)

            group = cmds.sets(

                empty=True, renderable=True, noSurfaceShader=True, name=self.name("colorSG")

            )

            cmds.connectAttr(shader + ".outColor", group + ".surfaceShader")

            cmds.sets(

                [s for s in shapes if cmds.nodeType(s) == "mesh"], edit=True, forceElement=group

            )



    def line(self, name, start, end, color, visible=None):

        group = cmds.group(empty=True, name=self.name(name + "_display"), parent=self.visuals)

        n = cmds.curve(name=self.name(name), degree=1, point=[(0, 0, 0), (1, 0, 0)])

        n = cmds.parent(n, group)[0]

        shape = cmds.listRelatives(n, shapes=True, fullPath=True)[0]

        self.plug(start, shape + ".controlPoints[0]")

        self.plug(end, shape + ".controlPoints[1]")

        cmds.setAttr(shape + ".lineWidth", 3)

        self.color(n, color)

        cmds.setAttr(n + ".overrideDisplayType", 0)

        if visible:

            cmds.connectAttr(visible, n + ".visibility")

        # Cone tip points away from the start; its constraint is a native DG node.

        # An invisible endpoint anchor avoids a sphere obscuring the arrowhead.

        tip = cmds.createNode("transform", name=self.name(name + "_tip"))

        tip = cmds.parent(tip, group)[0]

        self.plug(end, tip + ".translate")

        self.color(tip, color)

        cmds.setAttr(tip + ".overrideDisplayType", 0)

        if visible:

            cmds.connectAttr(visible, tip + ".visibility")

        start_node = cmds.createNode(

            "transform", name=self.name(name + "_start"), parent=group

        )

        self.plug(start, start_node + ".translate")

        cone = cmds.polyCone(

            name=self.name(name + "_arrowhead"),

            radius=0.10,

            height=0.30,

            subdivisionsX=12,

            constructionHistory=False,

        )[0]

        cone = cmds.parent(cone, tip, relative=True)[0]

        # Leave the exact endpoint clear for locators and other meeting vectors.

        # Move vertices in object space so the aim constraint preserves this gap.

        cmds.move(0, -0.35, 0, cone + ".vtx[*]", relative=True, objectSpace=True)

        cmds.aimConstraint(

            start_node,

            cone,

            name=self.name(name + "_aim"),

            aimVector=(0, -1, 0),

            upVector=(0, 0, 1),

            worldUpType="none",

        )

        self.color(cone, color)

        cmds.setAttr(cone + ".overrideDisplayType", 0)

        # Short arrows shrink instead of leaving an oversized, reversed-looking head.

        delta = self.vector(name + "_delta", end, start, 2)

        length = self.magnitude(name + "_size", delta)

        scale = self.node("multiplyDivide", name + "_head_scale")

        self.plug(length, scale + ".input1X")

        cmds.setAttr(scale + ".input2X", 0.8)

        clamp = self.node("clamp", name + "_head_limit")

        cmds.setAttr(clamp + ".maxR", 1)

        self.plug(scale + ".outputX", clamp + ".inputR")

        for axis in "XYZ":

            self.plug(clamp + ".outputR", cone + ".scale" + axis)

        cmds.setAttr(group + ".overrideEnabled", True)

        # Reference curves are omitted by ornament-free playblasts in Maya 2027.

        # Keep the line drawable and protect its transform with channel locks.

        cmds.setAttr(group + ".overrideDisplayType", 0)

        cmds.setAttr(n + ".overrideDisplayType", 0)

        lock_channels(n, "trs")

        return n



    def diagnostics(self):

        s, e, w = [self.world(p, label) for p, label in zip(self.points, ["S", "E", "W"])]

        a = self.vector("upper_displacement", e, s, 2)

        b = self.vector("lower_displacement", w, e, 2)

        u = self.product("upper_unit", a, normalize=True)

        v = self.product("lower_unit", b, normalize=True)

        self.dot = self.product("raw_dot", a, b, 1)

        self.cosine = self.product("cosine", u, v, 1)

        normal = self.product("raw_cross", a, b, 2)

        cross_unit = self.product("normal_unit", normal, normalize=True)

        normalized_cross = self.product("relative_cross", u, v, 2)

        valid_cross = self.valid("plane_valid", self.magnitude("relative_area", normalized_cross))

        self.line("upper_vector", s, e, (0.1, 0.8, 0.65),

                  self.valid("upper_arrow_valid", self.magnitude("upper_arrow_length", a)))

        self.line("lower_vector", e, w, (0.95, 0.65, 0.1),

                  self.valid("lower_arrow_valid", self.magnitude("lower_arrow_length", b)))

        self.line(

            "unit_vector",

            s,

            self.vector("unit_end", s, u),

            (0.3, 0.6, 1),

            self.valid("upper_valid", self.magnitude("upper_length", a)),

        )

        normal_display = self.node("multiplyDivide", "normal_display_scale")

        self.plug(cross_unit, normal_display + ".input1")

        cmds.setAttr(normal_display + ".input2", 3,3,3,type="double3")

        self.line(

            "plane_normal", e, self.vector("normal_end", e, normal_display + ".output"), (1, 0.25, 0.4), valid_cross

        )

        guide = self.vector("shoulder_wrist", w, s, 2)

        gu = self.product("guide_unit", guide, normalize=True)

        dp = self.product("projected_distance", a, gu, 1)

        mul = self.node("multiplyDivide", "projected_vector")

        self.plug(gu, mul + ".input1")

        for axis in "XYZ":

            self.plug(dp + "X", mul + ".input2" + axis)

        self.projection = self.vector("H", s, mul + ".output")

        valid_guide = self.valid("guide_valid", self.magnitude("guide_length", guide))

        self.line("guide", s, w, (0.5, 0.5, 0.5), valid_guide)

        self.line("projection", s, self.projection, (0.6, 0.4, 1), valid_guide)

        self.line("bend_residual", self.projection, e, (1, 0.4, 0.8), valid_guide)

        self.line("sum_vector", s, w, (0.65, 0.9, 0.35), valid_guide)

        # Native annotation anchors follow the DG. The open tool refreshes their

        # coordinate text; the last displayed values are saved with the scene.

        for label, value, offset in [("S", s, (-1.05,-0.25,0)),

                                     ("E", e, (0,0.4,0)),

                                     ("W", w, (0.7,0.45,0))]:

            self.label(label, label, value, offset)

        for label, start, end, parent, offset in [("a",s,e,"upper_vector_display",(-0.4,0.1,0)), ("b",e,w,"lower_vector_display",(0.35,0.15,0))]:

            mid = self.node("multiplyDivide", label + "_midpoint")

            self.plug(self.vector(label + "_ends", start, end), mid + ".input1")

            cmds.setAttr(mid + ".input2", 0.5,0.5,0.5,type="double3")

            self.label(label, label, mid + ".output", offset, parent)

        # The midpoint is an average, not a unit direction.

        midpoint = self.node("multiplyDivide", "sum_midpoint")

        self.plug(self.vector("sum_ends", s, w), midpoint + ".input1")

        cmds.setAttr(midpoint + ".input2", 0.5,0.5,0.5, type="double3")

        self.label("sum", "a + b", midpoint + ".output", (0,-0.5,0), "sum_vector_display", valid_guide)

        self.label("guide", "g = W - S (S to W)", w, (0.8,-0.7,0), "guide_display", valid_guide)

        projection_mid = self.node("multiplyDivide", "projection_midpoint")

        self.plug(self.vector("projection_ends", s, self.projection), projection_mid + ".input1")

        cmds.setAttr(projection_mid + ".input2", .5,.5,.5,type="double3")

        self.label("projected", "p = H - S = k u", projection_mid + ".output", (0,-.65,0), "projection_display", valid_guide)

        residual_mid = self.node("multiplyDivide", "residual_midpoint")

        self.plug(self.vector("residual_ends", self.projection, e), residual_mid + ".input1")

        cmds.setAttr(residual_mid + ".input2", .5,.5,.5,type="double3")

        self.label("residual", "r = E - H", residual_mid + ".output", (.5,0,0), "bend_residual_display", valid_guide)

        self.label("H", "H (point)", self.projection, (0,-0.7,0), "projection_display")

        self.label("unit", "u", self.name("unit_end") + ".output3D", (-0.25,0.25,0), "unit_vector_display", self.name("upper_valid") + ".outColorR")

        self.label("normal", "n = unit(a x b), drawn 3x", self.name("normal_end") + ".output3D", (0.6,0.6,0), "plane_normal_display", valid_cross)



    def label(self, name, text, position, offset, parent_name=None, visible=None):

        parent = self.name(parent_name) if parent_name else self.visuals

        transform = cmds.createNode("transform", name=self.name(name + "_label"), parent=parent)

        shape = cmds.createNode("annotationShape", name=self.name(name + "_labelShape"), parent=transform)

        cmds.setAttr(shape + ".text", text, type="string")

        cmds.setAttr(shape + ".displayArrow", False)

        self.plug(self.vector(name + "_label_offset", position, offset), transform + ".translate")

        cmds.setAttr(shape + ".overrideEnabled", True)

        cmds.setAttr(shape + ".overrideRGBColors", True)

        cmds.setAttr(shape + ".overrideColorRGB", *{"S":(1,.4,.4), "E":(.4,1,.45), "W":(.4,.65,1), "a":(.1,.8,.65), "b":(.95,.65,.1), "guide":(.7,.7,.7), "H":(.6,.4,1), "projected":(.6,.4,1), "residual":(1,.4,.8), "normal":(1,.25,.4)}.get(name,(.95,.95,.95)))

        if visible:

            self.plug(visible, transform + ".visibility")

        lock_channels(transform, "trs")



    def readout(self):

        values = [cmds.xform(p, query=True, worldSpace=True, translation=True) for p in self.points]

        data = analyze(*values)

        data.update(points=values, units=cmds.currentUnit(query=True, linear=True))

        return data



    def update_point_labels(self, data=None):

        """Show the same world positions as the math panel, without undo noise."""

        from .calculations import vector

        if self.mode == "rotations":

            return

        data = self.readout() if data is None else data

        labels = list(zip("SEW", data["points"])) + [("H", data["projection"])]

        changes = []

        for label, point in labels:

            shape = self.name(label + "_labelShape")

            text = label + " " + (vector(point) if point is not None else "(undefined)")

            if cmds.objExists(shape) and cmds.getAttr(shape + ".text") != text:

                changes.append((shape, text))

        if not changes:

            return

        undo_enabled = cmds.undoInfo(query=True, state=True)

        try:

            cmds.undoInfo(stateWithoutFlush=False)

            for shape, text in changes:

                cmds.setAttr(shape + ".text", text, type="string")

        finally:

            cmds.undoInfo(stateWithoutFlush=undo_enabled)



    def display(self, topic):

        """Topic visibility is independent of the DG's zero-length guards."""

        self.topic = topic

        # Apply the label spacing to previously built/saved lessons too.

        s_offset = self.name("S_label_offset")

        if cmds.objExists(s_offset):

            cmds.setAttr(s_offset + ".input3D[1]", -1.05, -.25, 0, type="double3")

        # Separate the unit comparison arrow from a, including restored scenes.

        # Translate the entire display, not the vector calculation or S/E.

        if cmds.objExists(self.name("unit_vector_display")):

            cmds.setAttr(self.name("unit_vector_display") + ".translate", -1.6, 0, 0)

        if cmds.objExists(self.name("unit_labelShape")):

            cmds.setAttr(self.name("unit_labelShape") + ".text", "u (length 1)", type="string")
            cmds.setAttr(self.name("unit_labelShape") + ".overrideColorRGB", .3, .6, 1)

        if cmds.objExists(self.name("H_label_offset")):
            cmds.setAttr(self.name("H_label_offset") + ".input3D[1]", 0, -1.3, 0, type="double3")
        # The matrix readout uses this local corner; make the same point visible.

        marker = self.name("local_point_marker")

        if self.mode == "rotations" and not cmds.objExists(marker):

            marker = cmds.polySphere(name=marker, radius=.08, subdivisionsX=12,

                                     subdivisionsY=8, constructionHistory=False)[0]

            cmds.parent(marker, self.hand, relative=True)

            cmds.setAttr(marker + ".translate", .9, .175, .5)

            self.color(marker, (1, .85, .1))

            shape = cmds.listRelatives(marker, shapes=True)[0]

            cmds.setAttr(shape + ".overrideEnabled", True)

            cmds.setAttr(shape + ".overrideDisplayType", 2)

            lock_channels(marker, "trs")

        # Refresh display wording on lessons restored from an older saved scene.

        for label, text in (("projected", "p = k u"), ("residual", "r = E - H")):

            shape = self.name(label + "_labelShape")

            if cmds.objExists(shape):

                cmds.setAttr(shape + ".text", text, type="string")

        sets = {

            "Step 1: S to E": ["upper_vector"],

            "Vectors": ["upper_vector", "lower_vector", "sum_vector"],

            "Normalize": ["upper_vector", "unit_vector"],

            "Dot / alignment": ["upper_vector", "lower_vector"],

            "Dot / projection": ["upper_vector", "lower_vector", "guide", "projection", "bend_residual"],

            "Cross / plane": ["upper_vector", "lower_vector", "plane_normal"],

            "Rig only": [],

        }

        active = sets[topic]

        for name in ["upper_vector", "lower_vector", "unit_vector", "plane_normal", "guide", "projection", "bend_residual", "sum_vector"]:

            if cmds.objExists(self.name(name + "_display")):

                cmds.setAttr(self.name(name + "_display") + ".visibility", name in active)

        cmds.setAttr(self.visuals + ".visibility", self.mode != "rotations")

        cmds.setAttr(self.rotation_parent + ".visibility", self.mode == "rotations")

        if self.mode == "vectors":

            show_w = topic not in ("Step 1: S to E", "Normalize")

            cmds.setAttr(self.points[2] + ".visibility", show_w)

            if cmds.objExists(self.name("W_label")):

                cmds.setAttr(self.name("W_label") + ".visibility", show_w)

            if not show_w and self.points[2] in (cmds.ls(selection=True) or []):

                cmds.select(clear=True)

        if self.mode == "rotations":

            for point in self.points:

                cmds.setAttr(point + ".visibility", False)

        self.update_point_labels()



    def set_ik(self, enabled):

        """Match the current pose before changing the single-chain teaching rig."""

        if self.mode != "arm":

            return

        if bool(cmds.getAttr(self.ik + ".ikBlend")) == bool(enabled):

            return

        with edit_chunk("Week 5 match FK IK"):

            data = self.readout()  # Force evaluation before sampling rotations.

            rotations = [cmds.xform(p, query=True, rotation=True, objectSpace=True) for p in self.points]

            if enabled:

                cmds.xform(self.target, worldSpace=True, translation=data["points"][2])

                helper = data["helper"]

                if helper is not None:

                    cmds.xform(self.pole, worldSpace=True, translation=helper)

            cmds.setAttr(self.ik + ".ikBlend", int(enabled))

            if not enabled:

                for point, rotation in zip(self.points, rotations):

                    cmds.xform(point, objectSpace=True, rotation=rotation)



    def healthy(self):

        required = [self.root, self.camera, self.hand, self.visuals] + self.points

        required += [self.name(name + "_display") for name in ["upper_vector", "lower_vector", "unit_vector", "plane_normal", "guide", "projection", "bend_residual"]]

        if self.mode == "arm":

            required += [self.ik, self.target, self.pole, self.name("target_constraint"), self.name("pole_constraint")]

        return all(cmds.objExists(node) for node in required)



    def preset(self, name="Bent arm"):

        if self.mode != "vectors":

            raise ValueError("Geometric presets belong to the locator sandbox.")

        with edit_chunk("Week 5 preset"):

            cmds.setAttr(self.root + ".translate", 0, 0, 0)

            cmds.setAttr(self.root + ".rotate", 0, 0, 0)

            cmds.setAttr(self.root + ".scale", 1, 1, 1)

            for p, xyz in zip(self.points, PRESETS[name]):

                cmds.xform(p, worldSpace=True, translation=xyz)



    def attachment(self, mode=None, visible=True):

        """Optional prop comparison on the wrist. Preserve pose when changing links."""

        if self.mode != "arm":

            raise ValueError("Attachments belong to the arm lesson.")

        prop = self.name("attachment_prop")

        before=set(cmds.ls(self.namespace+":*") or [])

        with edit_chunk("Week 5 attachment"):

            if not cmds.objExists(prop):

                prop = cmds.polyCube(name=prop, width=0.6, height=0.6, depth=0.65, constructionHistory=False)[0]

                cmds.parent(prop, self.points[-1], relative=True)

                cmds.setAttr(prop + ".translate", .7,-.42,0)

                cmds.parent(prop, self.root)  # preserve the initial grip pose in world space

                self.color(prop, (0.75,0.75,0.75))

                cmds.addAttr(prop, longName="attachmentMode", dataType="string")

                cmds.setAttr(prop + ".attachmentMode", "World (unattached)", type="string")

                shape = cmds.listRelatives(prop, shapes=True)[0]

                cmds.setAttr(shape + ".overrideEnabled", True)

                cmds.setAttr(shape + ".overrideDisplayType", 0)

                cmds.setAttr(prop+".displayLocalAxis",True)

                self.line("prop_link",self.world(self.points[-1],"prop_wrist_world"),self.world(prop,"prop_world"),(.7,.7,.7))

                self.label("prop_info","Prop",self.world(prop,"prop_info_world"),(2,1.5,0),"prop_link_display")

            cmds.setAttr(self.name("prop_link_display")+".visibility",visible)

            cmds.setAttr(prop + ".visibility", visible)

            if mode is not None:

                world = cmds.xform(prop, query=True, worldSpace=True, matrix=True)

                constraint = self.name("attachment_constraint")

                if cmds.objExists(constraint):

                    cmds.delete(constraint)

                cmds.parent(prop, self.root) if cmds.listRelatives(prop,parent=True)[0] != self.root else None

                cmds.xform(prop, worldSpace=True, matrix=world)

                if mode == "Hierarchy parent":

                    cmds.parent(prop, self.points[-1])

                elif mode != "World (unattached)":

                    operation = {"Point constraint":cmds.pointConstraint,"Orient constraint":cmds.orientConstraint,"Parent constraint":cmds.parentConstraint}[mode]

                    operation(self.points[-1], prop, maintainOffset=True, name=constraint)

                cmds.setAttr(prop + ".attachmentMode", mode, type="string")

                cmds.setAttr(self.name("prop_info_labelShape")+".text","Prop | "+mode,type="string")

            # Remember only the nodes this operation added, for scoped reset.

            registry = self.name("lesson_state")

            data = json.loads(cmds.getAttr(registry + ".week05Data"))

            names = list(set(cmds.ls(self.namespace+":*") or [])-before) + [prop] + (cmds.listRelatives(prop, allDescendents=True, fullPath=True) or [])

            names += cmds.ls(self.name("attachment_constraint")) or []

            # The prop's shader was generated by color(); capture its network too.

            shapes = cmds.listRelatives(prop, shapes=True, fullPath=True) or []

            for shape in shapes:

                for sg in cmds.listConnections(shape, type="shadingEngine") or []:

                    if sg.startswith(self.namespace + ":"):

                        names.append(sg)

                        names += cmds.listConnections(sg + ".surfaceShader", source=True, destination=False) or []

            self.owned = list(set(data["owned"] + (cmds.ls(names, uuid=True) or [])))

            data["owned"] = self.owned

            cmds.setAttr(registry + ".week05Data", json.dumps(data), type="string")

        return prop



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





def build(mode="vectors"):

    if mode not in ("vectors", "arm", "rotations"):

        raise ValueError("Choose vectors, arm or rotations.")

    if cmds.currentUnit(query=True, linear=True) != "cm":

        raise ValueError(

            "Use a centimeter teaching scene for the known-answer presets. Scene units were not changed."

        )

    previous_namespace = cmds.namespaceInfo(currentNamespace=True)

    with edit_chunk("Build Week 5 " + mode):

        cmds.namespace(setNamespace=":")

        index = 1

        while cmds.namespace(exists="Week05_{}".format(index)):

            index += 1

        ns = "Week05_{}".format(index)

        cmds.namespace(add=ns)

        demo = Demo(ns, mode)

        try:

            demo.root = cmds.group(empty=True, name=demo.root)

            cmds.addAttr(demo.root, longName="week05Mode", dataType="string")

            cmds.setAttr(demo.root + ".week05Mode", mode, type="string", lock=True)

            demo.visuals = cmds.group(empty=True, name=demo.name("WORLD_visuals"), parent=demo.root)

            cmds.setAttr(demo.visuals + ".inheritsTransform", False)

            if mode != "arm":

                for label, xyz in zip(["S", "E", "W"], PRESETS["Bent arm"]):

                    p = cmds.spaceLocator(name=demo.name(label))[0]

                    p = cmds.parent(p, demo.root)[0]

                    cmds.xform(p, worldSpace=True, translation=xyz)

                    shape = cmds.listRelatives(p, shapes=True)[0]

                    for axis in "XYZ":

                        cmds.setAttr(shape + ".localScale" + axis, 0.2)

                    demo.color(p, {"S":(1,.4,.4),"E":(.4,1,.45),"W":(.4,.65,1)}[label])

                    demo.points.append(p)

            else:

                demo.points = create_arm_chain(demo.name, demo.root, PRESETS["Bent arm"])

                for p in demo.points:

                    cmds.setAttr(p + ".displayLocalAxis", False)

                    cmds.setAttr(p + ".drawStyle", 2)

                for i, joint in enumerate(demo.points[:2]):

                    mesh = cmds.polyCube(

                        name=demo.name("segment{}".format(i)),

                        width=4.5,

                        height=0.4,

                        depth=0.6,

                        constructionHistory=False,

                    )[0]

                    cmds.parent(mesh, joint, relative=True)

                    cmds.setAttr(mesh + ".translateX", 2.5)

                    demo.color(mesh, (0.15, 0.4, 0.45) if i == 0 else (0.55, 0.38, 0.13))

                wrist_hand = cmds.polyCube(

                    name=demo.name("rig_hand"),

                    width=1.2,

                    height=0.3,

                    depth=0.8,

                    constructionHistory=False,

                )[0]

                cmds.parent(wrist_hand, demo.points[-1], relative=True)

                cmds.setAttr(wrist_hand + ".translateX", 0.7)

                demo.color(wrist_hand, (0.3, 0.6, 0.7))

                demo.target = cmds.circle(

                    name=demo.name("IK_target"),

                    normal=(1, 0, 0),

                    radius=0.8,

                    constructionHistory=False,

                )[0]

                cmds.parent(demo.target, demo.root)

                cmds.xform(demo.target, worldSpace=True, translation=(6, 0, 0))

                demo.pole = cmds.circle(

                    name=demo.name("pole_control"),

                    normal=(0, 0, 1),

                    radius=0.5,

                    constructionHistory=False,

                )[0]

                cmds.parent(demo.pole, demo.root)

                cmds.xform(demo.pole, worldSpace=True, translation=(3, 6, 0))

                demo.ik = create_arm_ik(demo.name, demo.root, demo.points, demo.target, demo.pole)

                demo.color(demo.target, (0.2, 0.8, 1))

                demo.color(demo.pole, (1, 0.4, 0.8))

                reverse = demo.node("reverse", "fk_visibility")

                cmds.connectAttr(demo.ik + ".ikBlend", reverse + ".inputX")

                for joint in demo.points:

                    control = cmds.circle(normal=(1, 0, 0), radius=0.75, constructionHistory=False)[0]

                    shape = cmds.listRelatives(control, shapes=True, fullPath=True)[0]

                    shape = cmds.parent(shape, joint, shape=True, relative=True)[0]

                    cmds.rename(shape, demo.name(joint.split(":")[-1] + "_FK_shape"))

                    cmds.delete(control)

                    shape = cmds.listRelatives(joint, shapes=True, fullPath=True)[0]

                    cmds.connectAttr(reverse + ".outputX", shape + ".visibility")

                    cmds.setAttr(shape + ".overrideEnabled", True)

                    cmds.setAttr(shape + ".overrideColor", 17)

                for control in [demo.target, demo.pole]:

                    cmds.connectAttr(demo.ik + ".ikBlend", control + ".visibility")

            demo.diagnostics()

            if mode == "arm":

                demo.line("pole_guide",demo.world(demo.points[1],"pole_elbow_world"),demo.world(demo.pole,"pole_guide_world"),(.75,.4,.65),demo.ik+".ikBlend")

                demo.label("pole", "Elbow pole", demo.world(demo.pole, "pole_label_world"), (0,0.5,0), visible=demo.ik + ".ikBlend")

            demo.rotation_parent = cmds.group(

                empty=True, name=demo.name("space_parent"), parent=demo.root

            )

            cmds.setAttr(demo.rotation_parent + ".translateY", -4)

            demo.hand = cmds.polyCube(

                name=demo.name("marked_hand"),

                width=1.8,

                height=0.35,

                depth=1,

                constructionHistory=False,

            )[0]

            cmds.parent(demo.hand, demo.rotation_parent, relative=True)

            cmds.setAttr(demo.hand + ".displayLocalAxis", True)

            rotation_labels=cmds.group(empty=True,name=demo.name("rotation_labels"),parent=demo.rotation_parent)

            cmds.setAttr(rotation_labels+".inheritsTransform",False)

            # Separated reference poses make the endpoint orientations readable.

            for label, x, rotation in [("start_pose",-3,(0,0,0)),("end_pose",3,(90,90,0))]:

                ghost=cmds.polyCube(name=demo.name(label),width=1.8,height=.35,depth=1,constructionHistory=False)[0]

                cmds.parent(ghost,demo.rotation_parent,relative=True)

                cmds.setAttr(ghost+".translateX",x)

                cmds.setAttr(ghost+".rotate",*rotation)

                shape=cmds.listRelatives(ghost,shapes=True)[0]

                cmds.setAttr(shape+".overrideEnabled",True)

                cmds.setAttr(shape+".overrideShading",True)

                demo.color(ghost,(.3,.35,.4))

                cmds.setAttr(shape+".overrideDisplayType",2)

                lock_channels(ghost,"trs")

                demo.label(label,"Start: t=0" if x<0 else "End: t=1",demo.world(ghost,label+"_world"),(0,1.8,0),parent_name="rotation_labels")

            demo.label("current_pose","Current orientation",demo.world(demo.hand,"current_pose_world"),(0,1.8,0),parent_name="rotation_labels")

            demo.camera = cmds.camera(name=demo.name("capture_camera"))[0]

            cmds.parent(demo.camera, demo.root)

            cmds.setAttr(demo.camera + ".inheritsTransform", False)

            cmds.setAttr(demo.camera + ".translate", 14, 10, 20)

            aim = cmds.createNode("transform", name=demo.name("camera_aim"), parent=demo.root)

            cmds.setAttr(aim + ".translate", 3, 0, 0)

            constraint = cmds.aimConstraint(

                aim, demo.camera, aimVector=(0, 0, -1), upVector=(0, 1, 0)

            )[0]

            cmds.delete(constraint)

            # Only purposeful controls are editable; meshes and arrows are reference display.

            for mesh in cmds.ls(ns + ":*", type="mesh") or []:

                parent = cmds.listRelatives(mesh, parent=True, fullPath=True)[0]

                if parent.split("|")[-1] != demo.hand:

                    cmds.setAttr(mesh + ".overrideEnabled", True)

                    cmds.setAttr(mesh + ".overrideDisplayType", 2)

                    lock_channels(parent, "trs")

            for point in demo.points:

                lock_channels(point, "ts" if mode == "arm" else "rs")

                if mode == "arm":

                    for axis in "XYZ":

                        cmds.setAttr(point + ".jointOrient" + axis, lock=True, keyable=False)

            if mode == "arm":

                for control in [demo.target, demo.pole]:

                    lock_channels(control, "rs")

                lock_channels(demo.root, "s")

            demo.display("Rig only" if mode == "arm" else "Vectors")

            registry = cmds.createNode("network", name=demo.name("lesson_state"))

            cmds.addAttr(registry, longName="week05Data", dataType="string")

            roles = {key: getattr(demo, key) for key in ["namespace", "mode", "root", "visuals", "points", "hand", "rotation_parent", "camera", "dot", "cosine", "projection"]}

            if mode == "arm":

                roles.update({key: getattr(demo, key) for key in ["ik", "target", "pole"]})

            roles["owned"] = cmds.ls(ns + ":*", uuid=True)

            cmds.setAttr(registry + ".week05Data", json.dumps(roles), type="string")

            demo.owned = roles["owned"]

            return demo

        finally:

            cmds.namespace(setNamespace=previous_namespace)





def lock_channels(node, channels):

    for channel in channels:

        for axis in "xyz":

            plug = node + "." + channel + axis

            cmds.setAttr(plug, lock=True, keyable=False, channelBox=False)





class Session:

    """Reuse one fixture per lesson, with undoable scoped reset. Survives UI reopen."""

    def __init__(self):

        self.demos = {}

        for registry in cmds.ls(type="network") or []:

            if not cmds.attributeQuery("week05Data", node=registry, exists=True):

                continue

            try:

                data = json.loads(cmds.getAttr(registry + ".week05Data"))

                demo = Demo(data["namespace"], data["mode"])

                demo.__dict__.update(data)

                self.demos[demo.mode] = demo

            except (ValueError, KeyError, RuntimeError):

                continue



    def switch(self, mode, reset=False):

        with edit_chunk("Week 5 lesson " + mode):

            demo = self.demos.get(mode)

            if reset and demo:

                # UUID ownership avoids deleting unrelated or newly added namespace nodes.

                owned = cmds.ls(demo.owned, long=True) or []

                owned_set = set(owned)

                # Teardown can temporarily disconnect normalizer inputs before their

                # nodes disappear. Disable normalization to avoid spurious Maya errors.

                for node in owned:

                    if cmds.nodeType(node) == "vectorProduct":

                        cmds.setAttr(node + ".normalizeOutput", False)

                for node in owned:

                    if cmds.objectType(node, isAType="transform"):

                        for child in cmds.listRelatives(node, children=True, fullPath=True) or []:

                            if child not in owned_set and cmds.objectType(child, isAType="transform"):

                                cmds.parent(child, world=True)

                cmds.delete(cmds.ls(demo.owned) or [])

                demo = None

            if demo is None:

                demo = build(mode)

                self.demos[mode] = demo

            for other in self.demos.values():

                if cmds.objExists(other.root):

                    cmds.setAttr(other.root + ".visibility", other is demo)

            return demo
