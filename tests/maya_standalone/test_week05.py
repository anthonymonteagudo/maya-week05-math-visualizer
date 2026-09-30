"""Run alone: mayapy -m unittest tests.maya_standalone.test_week05."""

import tempfile
import unittest
from pathlib import Path

import maya.standalone

maya.standalone.initialize(name="python")
from maya import cmds  # noqa: E402
from maya.api import OpenMaya as om  # noqa: E402

from lesson_materials.week_05_applied_math.scene import build, Session  # noqa: E402


class Week05Tests(unittest.TestCase):
    def setUp(self):
        cmds.file(new=True, force=True)

    def test_controls_and_mode_matching(self):
        d = build("arm")
        self.assertEqual(cmds.getAttr(d.ik + ".ikBlend"), 1)
        cmds.setAttr(d.target + ".translate", 5, 1, 1)
        before = d.readout()["points"]
        d.set_ik(False)
        for a, b in zip(before, d.readout()["points"]):
            self.vector_equal(a, b)
        self.assertFalse(cmds.getAttr(d.target + ".visibility"))
        cmds.setAttr(d.points[0] + ".rotateZ", 15)
        before = d.readout()["points"]
        d.set_ik(True)
        for a, b in zip(before, d.readout()["points"]):
            for x, y in zip(a, b):
                self.assertAlmostEqual(x, y, delta=0.001)
        with self.assertRaises(RuntimeError):
            cmds.setAttr(d.points[1] + ".translateX", 30)
        with self.assertRaises(RuntimeError):
            cmds.setAttr(d.name("segment0") + ".translateY", 30)
        self.assertFalse(cmds.getAttr(d.rotation_parent + ".visibility"))

    def test_switch_reset_reopen_and_repair(self):
        session = Session()
        vectors = session.switch("vectors")
        arm = session.switch("arm")
        self.assertFalse(cmds.getAttr(vectors.root + ".visibility"))
        self.assertEqual(session.switch("vectors").root, vectors.root)
        self.assertEqual(Session().switch("arm").root, arm.root)
        extra = cmds.createNode("transform", name="user_content", parent=arm.root)
        sentinel = cmds.createNode("transform", name="outside")
        cmds.delete(arm.target)
        self.assertFalse(arm.healthy())
        new = session.switch("arm", reset=True)
        self.assertTrue(new.healthy())
        self.assertTrue(cmds.objExists(extra))
        self.assertTrue(cmds.objExists(sentinel))
        self.assertFalse(cmds.objExists(arm.root))
        self.assertEqual(len(Session().demos), 2)
        rotations = session.switch("rotations")
        self.assertTrue(cmds.getAttr(rotations.rotation_parent + ".visibility"))
        self.assertFalse(cmds.getAttr(rotations.visuals + ".visibility"))
        self.assertFalse(cmds.getAttr(new.root + ".visibility"))

    def test_pole_and_reach(self):
        d = build("arm")
        before = d.readout()["points"][1]
        cmds.setAttr(d.pole + ".translate", 3, 0, 6)
        after = d.readout()
        self.assertGreater(abs(after["points"][1][2] - before[2]), 1)
        self.vector_equal(after["points"][2], (6, 0, 0))
        cmds.setAttr(d.target + ".translateX", 20)
        after = d.readout()
        self.assertAlmostEqual(after["upper_length"], 5)
        self.assertAlmostEqual(after["lower_length"], 5)

    def vector_equal(self, a, b):
        for x, y in zip(a, b):
            self.assertAlmostEqual(x, y, places=5)

    def test_bake_is_independent_and_samples_match(self):
        from lesson_materials.week_05_applied_math.animation import bake_comparison, rotation_at
        d=build("rotations")
        original=cmds.getAttr(d.hand+".rotate")
        group=bake_comparison(start=1,frames=4)
        boxes=cmds.listRelatives(group,children=True,type="transform")
        self.assertEqual(len(boxes),2)
        self.assertEqual(cmds.getAttr(d.hand+".rotate"),original)
        for box in boxes:
            method="slerp" if "slerp" in box else "euler"
            actual=cmds.getAttr(box+".rotate",time=3)[0]
            for x,y in zip(actual,rotation_at(.5,method)):self.assertAlmostEqual(x,y)
            self.assertEqual(cmds.keyframe(box,q=True,attribute="rotateX",keyframeCount=True),5)

    def test_rotation_references_and_grip(self):
        d=build("rotations")
        self.assertTrue(cmds.objExists(d.name("start_pose")))
        self.assertEqual(cmds.getAttr(d.name("end_pose")+".rotate")[0],(90,90,0))
        d.interpolate(.5)
        self.assertEqual(cmds.getAttr(d.name("start_pose")+".rotate")[0],(0,0,0))
        d=build("arm")
        prop=d.attachment("Hierarchy parent")
        for actual,expected in zip(cmds.getAttr(prop+".translate")[0],(.7,-.42,0)):
            self.assertAlmostEqual(actual,expected,places=5)
        self.assertIn("Hierarchy parent",cmds.getAttr(d.name("prop_info_labelShape")+".text"))
        d.attachment(visible=False)
        self.assertFalse(cmds.getAttr(d.name("prop_link_display")+".visibility"))

    def test_normal_display_and_fk_wrist(self):
        d = build("vectors")
        endpoint = cmds.getAttr(d.name("normal_end") + ".output3D")[0]
        e = d.readout()["points"][1]
        self.assertAlmostEqual(sum((x-y)**2 for x,y in zip(endpoint,e)),9)
        self.assertAlmostEqual(sum(x*x for x in d.readout()["normal"]),1)
        d = build("arm")
        d.set_ik(False)
        positions = d.readout()["points"]
        hand = cmds.xform(d.name("rig_hand"),q=True,ws=True,matrix=True)
        cmds.setAttr(d.points[-1]+".rotateX",35)
        self.assertEqual(d.readout()["points"],positions)
        self.assertNotEqual(cmds.xform(d.name("rig_hand"),q=True,ws=True,matrix=True),hand)
        self.assertTrue(cmds.objExists(d.name("wrist_FK_shape")))
        prop=d.attachment("Orient constraint")
        shape=cmds.listRelatives(prop,shapes=True)[0]
        self.assertEqual(cmds.getAttr(shape+".overrideDisplayType"),0)
        cmds.setAttr(prop+".translateY",7)
        self.assertAlmostEqual(cmds.getAttr(prop+".translateY"),7)

    def test_live_graph_and_world_frame(self):
        d = build()
        self.vector_equal(cmds.getAttr(d.projection)[0], (3, 0, 0))
        cmds.setAttr(d.points[1] + ".translateY", 2)
        self.assertAlmostEqual(cmds.getAttr(d.dot + "X"), 5)
        cmds.setAttr(d.root + ".translate", 10, 20, 30)
        self.vector_equal(cmds.xform(d.camera, query=True, worldSpace=True, translation=True), (14, 10, 20))
        self.vector_equal(cmds.getAttr(d.projection)[0], (13, 20, 30))
        self.vector_equal(
            cmds.pointPosition(d.name("upper_vector") + ".cv[0]", world=True), (10, 20, 30)
        )
        self.vector_equal(cmds.xform(d.name("E_label"), query=True, worldSpace=True, translation=True), (13,22.4,30))
        self.vector_equal(cmds.pointPosition(d.name("sum_vector") + ".cv[1]", world=True), (16,20,30))
        self.assertEqual(cmds.getAttr(d.name("W_labelShape") + ".text"), "W (6, 0, 0)")
        self.assertEqual(cmds.getAttr(d.name("a_labelShape") + ".text"), "a")

    def test_normalize_hides_unused_point_and_restores_it(self):
        d = build()
        cmds.select(d.points[2])
        d.display("Normalize")
        self.assertFalse(cmds.getAttr(d.points[2] + ".visibility"))
        self.assertFalse(cmds.getAttr(d.name("W_label") + ".visibility"))
        self.assertEqual(cmds.ls(selection=True), [])
        d.display("Vectors")
        self.assertTrue(cmds.getAttr(d.points[2] + ".visibility"))
        self.assertTrue(cmds.getAttr(d.name("W_label") + ".visibility"))

    def test_attachment_following_and_reset(self):
        session = Session()
        d = session.switch("arm")
        prop = d.attachment("World (unattached)")
        for mode in ["Hierarchy parent", "Point constraint", "Orient constraint", "Parent constraint", "World (unattached)"]:
            before = cmds.xform(prop, query=True, worldSpace=True, matrix=True)
            d.attachment(mode)
            self.vector_equal(before, cmds.xform(prop, query=True, worldSpace=True, matrix=True))
        d.attachment("Point constraint")
        pos = cmds.xform(prop, query=True, worldSpace=True, translation=True)
        rot = cmds.xform(prop, query=True, worldSpace=True, rotation=True)
        cmds.setAttr(d.target + ".translateY", 1)
        for actual,expected in zip(cmds.xform(prop, query=True, worldSpace=True, translation=True), (pos[0],pos[1]+1,pos[2])):
            self.assertAlmostEqual(actual, expected, delta=0.001)  # Native IK solve tolerance.
        self.vector_equal(cmds.xform(prop, query=True, worldSpace=True, rotation=True), rot)
        d.attachment("Orient constraint")
        pos = cmds.xform(prop, query=True, worldSpace=True, translation=True)
        before_rotation = cmds.xform(prop, query=True, worldSpace=True, rotation=True)
        cmds.setAttr(d.target + ".translateY", 2)
        self.vector_equal(cmds.xform(prop, query=True, worldSpace=True, translation=True), pos)
        self.assertGreater(sum(abs(a-b) for a,b in zip(before_rotation, cmds.xform(prop, query=True, worldSpace=True, rotation=True))), 0.01)
        d.attachment("Parent constraint")
        wrist = cmds.getAttr(d.points[-1] + ".worldMatrix[0]")
        relative = om.MMatrix(cmds.getAttr(prop + ".worldMatrix[0]")) * om.MMatrix(wrist).inverse()
        cmds.setAttr(d.target + ".translateY", 3)
        expected = relative * om.MMatrix(cmds.getAttr(d.points[-1] + ".worldMatrix[0]"))
        self.assertTrue(expected.isEquivalent(om.MMatrix(cmds.getAttr(prop + ".worldMatrix[0]")), 1e-5))
        session.switch("arm", reset=True)
        self.assertFalse(cmds.objExists(prop))
        self.assertFalse(cmds.objExists(d.name("attachment_constraint")))

    def test_degenerate_visibility(self):
        d = build()
        d.preset("Straight")
        self.assertFalse(cmds.getAttr(d.name("plane_normal") + ".visibility"))
        d.preset("Coincident shoulder/wrist")
        self.assertFalse(cmds.getAttr(d.name("projection") + ".visibility"))

    def test_arm_ik_and_lengths(self):
        d = build("arm")
        cmds.setAttr(d.ik + ".ikBlend", 1)
        cmds.setAttr(d.target + ".translate", 5, 1, 1)
        result = d.readout()
        for actual, expected in zip(result["points"][2], (5, 1, 1)):
            self.assertAlmostEqual(actual, expected, delta=1e-3)  # IK solver tolerance, cm.
        self.assertAlmostEqual(result["upper_length"], 5)
        self.assertAlmostEqual(result["lower_length"], 5)

    def test_namespace_selection_and_undo(self):
        sentinel = cmds.createNode("transform", name="week05_test_sentinel")
        cmds.select(sentinel)
        a = build()
        b = build()
        self.assertNotEqual(a.namespace, b.namespace)
        self.assertEqual(cmds.ls(selection=True), [sentinel])
        cmds.undo()
        self.assertFalse(cmds.objExists(b.root))
        self.assertTrue(cmds.objExists(a.root))
        self.assertTrue(cmds.objExists(sentinel))

    def test_interpolation_and_matrix_roundtrip(self):
        d = build()
        d.interpolate(0.5, "euler")
        half_euler = om.MTransformationMatrix(om.MMatrix(cmds.getAttr(d.hand + ".matrix"))).rotation(asQuaternion=True)
        d.interpolate(0.5, "slerp")
        half_slerp = om.MTransformationMatrix(om.MMatrix(cmds.getAttr(d.hand + ".matrix"))).rotation(asQuaternion=True)
        self.assertFalse(half_euler.isEquivalent(half_slerp, 1e-6))
        self.assertEqual(cmds.getAttr(d.hand + ".translateX"), 0)
        d.interpolate(1, "slerp")
        endpoint = om.MEulerRotation(om.MAngle(90, om.MAngle.kDegrees).asRadians(), om.MAngle(90, om.MAngle.kDegrees).asRadians(), 0).asQuaternion()
        self.assertTrue(endpoint.isEquivalent(om.MQuaternion(0.5,0.5,-0.5,0.5), 1e-6))
        q1 = om.MTransformationMatrix(om.MMatrix(cmds.getAttr(d.hand + ".matrix"))).rotation(
            asQuaternion=True
        )
        d.interpolate(1, "euler")
        q2 = om.MTransformationMatrix(om.MMatrix(cmds.getAttr(d.hand + ".matrix"))).rotation(
            asQuaternion=True
        )
        self.assertTrue(q1.isEquivalent(q2, 1e-6))
        cmds.setAttr(d.rotation_parent + ".rotateZ", 90)
        matrix = om.MMatrix(cmds.getAttr(d.hand + ".worldMatrix[0]"))
        p = om.MPoint(1, 2, 3)
        self.assertTrue(((p * matrix) * matrix.inverse()).isEquivalent(p, 1e-6))

    def test_saved_graph_evaluates_without_ui(self):
        d = build()
        name = d.name("raw_dot")
        with tempfile.TemporaryDirectory() as folder:
            target = str(Path(folder) / "math.ma")
            cmds.file(rename=target)
            cmds.file(save=True, type="mayaAscii")
            cmds.file(target, open=True, force=True)
            self.assertAlmostEqual(cmds.getAttr(name + ".outputX"), -7)


if __name__ == "__main__":
    unittest.main()
