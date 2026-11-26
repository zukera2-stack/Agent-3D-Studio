import unittest
from a3ds.linked_editor import Session, handles, drag_values
from a3ds.camera import standard_views
from a3ds.project import demo_project


class LinkedEditorTests(unittest.TestCase):
    def setUp(self):
        self.session = Session(demo_project())
        self.cameras = standard_views(420,300)

    def test_side_center(self):
        s = self.session.project.sections[3]
        c = self.cameras["side"]
        v = drag_values(s,c,"side","center",.2*c.pixels_per_unit,-.1*c.pixels_per_unit)
        self.assertAlmostEqual(v["y"],s.y+.2)
        self.assertAlmostEqual(v["center_z"],s.center_z+.1)
        self.assertEqual(v["half_width"],s.half_width)

    def test_front_width_sign(self):
        s = self.session.project.sections[-1]
        c = self.cameras["front"]
        v = drag_values(s,c,"front","width",-c.pixels_per_unit*.1,0)
        self.assertAlmostEqual(v["half_width"],s.half_width+.1)

    def test_linked_handle_move_and_history(self):
        old = self.session.project.as_dict()
        c = self.cameras["top"]
        before = handles(self.session.project,c,"top")
        s = self.session.project.sections[3]
        v = drag_values(s,c,"top","width",.1*c.pixels_per_unit,0)
        self.session.apply(3,v)
        new = self.session.project.as_dict()
        self.assertNotEqual(old,new)
        self.assertNotEqual(before,handles(self.session.project,c,"top"))
        self.session.undo()
        self.assertEqual(old,self.session.project.as_dict())
        self.session.redo()
        self.assertEqual(new,self.session.project.as_dict())

    def test_rejected_move_is_atomic(self):
        old = self.session.project.as_dict()
        c = self.cameras["side"]
        v = drag_values(self.session.project.sections[3],c,"side","center",1000,0)
        with self.assertRaises(ValueError):
            self.session.apply(3,v)
        self.assertEqual(old,self.session.project.as_dict())
        self.assertEqual([],self.session.history)

    def test_front_only_foremost(self):
        result = handles(self.session.project,self.cameras["front"],"front")
        self.assertEqual(len(result),3)
        self.assertTrue(all(r[0]==len(self.session.project.sections)-1 for r in result))
