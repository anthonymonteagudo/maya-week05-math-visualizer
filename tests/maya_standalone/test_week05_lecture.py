"""Run with mayapy -m unittest tests.maya_standalone.test_week05_lecture."""
import unittest
import maya.standalone
maya.standalone.initialize(name='python')
from maya import cmds
from lesson_materials.week_05_applied_math import lecture, scene, calculations, presentation


class LectureTests(unittest.TestCase):
    def test_camera_frame_changes_coordinates_without_moving_point(self):
        from lesson_materials.week_05_applied_math import spaces
        demo=scene.build('rotations')
        lecture.apply(demo,dict(space='camera'))
        self.assertIn('(3, 2, -6)',spaces.worked(demo))
        original=cmds.xform(demo.space_point,q=True,ws=True,translation=True)
        cmds.setAttr(demo.space_frame+'.translateX',2)
        self.assertEqual(original,cmds.xform(demo.space_point,q=True,ws=True,translation=True))
        self.assertIn('(2, 2, -6)',spaces.worked(demo))
        cmds.setAttr(demo.space_frame+'.rotateY',90)
        self.assertIn('= (6, 2, 2)',spaces.worked(demo))
        lecture.apply(demo,{})
        self.assertFalse(cmds.objExists(demo.name('space_demo')))
        self.assertTrue(cmds.getAttr(demo.rotation_parent+'.visibility'))

    def test_movement_known_answers_and_zero_direction(self):
        demo=scene.build('vectors')
        recipe=next(v for v in lecture.STEPS[2]['variations'] if v.get('movement')==(2,.5))
        lecture.apply(demo,recipe)
        text=calculations.movement(demo.readout(),2,.5)
        self.assertIn('New position = S + movement = (0.6, 0.8, 0)',text)
        cmds.setAttr(demo.root+'.translate',10,20,30)
        text=calculations.movement(demo.readout(),2,.5)
        self.assertIn('New position = S + movement = (10.6, 20.8, 30)',text)
        cmds.setAttr(demo.points[1]+'.translate',0,0,0)
        self.assertIn('UNDEFINED direction',calculations.movement(demo.readout(),2,.5))

    def test_coordinate_labels_follow_world_positions_without_undo_noise(self):
        demo=scene.build('vectors')
        demo.display('Step 1: S to E')
        self.assertEqual(cmds.getAttr(demo.name('E_labelShape')+'.text'),'E (3, 4, 0)')
        cmds.setAttr(demo.root+'.translate',10,20,30)
        undo_name=cmds.undoInfo(query=True,undoName=True)
        demo.update_point_labels()
        self.assertEqual(cmds.getAttr(demo.name('S_labelShape')+'.text'),'S (10, 20, 30)')
        self.assertEqual(cmds.getAttr(demo.name('E_labelShape')+'.text'),'E (13, 24, 30)')
        self.assertEqual(cmds.undoInfo(query=True,undoName=True),undo_name)
        cmds.undo()
        demo.update_point_labels()
        self.assertEqual(cmds.getAttr(demo.name('E_labelShape')+'.text'),'E (3, 4, 0)')

    def test_all_recipes_and_return_to_start(self):
        session=scene.Session()
        for step in lecture.STEPS:
            demo=session.switch(step['mode'])
            for variation in step['variations']:
                with self.subTest(step=step['label'], variation=variation['label']):
                    lecture.apply(demo,variation)
                    if demo.mode=='vectors':
                        data=demo.readout()
                        self.assertEqual([tuple(x) for x in data['points']],list(variation['points']))
                        text=calculations.vectors(data,variation['topic'])
                        self.assertTrue(presentation.document(text,data,variation['topic']))
                        if variation['topic']=='Dot / alignment':
                            self.assertNotIn('PROJECTION',text)
                            self.assertFalse(cmds.getAttr(demo.name('projection_display')+'.visibility'))
                    elif demo.mode=='rotations':
                        self.assertEqual(bool(cmds.getAttr(demo.name('start_pose')+'.visibility')),variation.get('view')==1)
                        if variation.get('view')==2:
                            self.assertAlmostEqual(cmds.getAttr(demo.hand+'.translateX'),4*variation['t'])
        demo=session.switch('vectors')
        lecture.apply(demo,lecture.STEPS[0]['variations'][0])
        self.assertFalse(cmds.getAttr(demo.points[2]+'.visibility'))
        self.assertFalse(cmds.getAttr(demo.name('unit_vector_display')+'.visibility'))


if __name__=='__main__':unittest.main()
