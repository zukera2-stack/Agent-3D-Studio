import unittest
from a3ds.editor import edit_section, orbit_camera, FIELDS
from a3ds.project import demo_project
from a3ds.raster import render_mesh


class EditorTests(unittest.TestCase):
    def setUp(self):
        self.project = demo_project()
        self.values = {k: getattr(self.project.sections[2],k) for k in FIELDS}

    def test_valid_edit(self):
        self.values["half_width"] *= 1.1
        edited = edit_section(self.project,2,self.values)
        self.assertNotEqual(edited.sections[2],self.project.sections[2])
        self.assertEqual(edited.sections[1],self.project.sections[1])
        self.assertTrue(edited.build().validate(require_closed=True,require_outward=True).ok)

    def test_invalid_edit_unchanged(self):
        original = self.project.as_dict()
        for field,value in (("half_width",0),("y",100),("center_z",float("nan"))):
            values = dict(self.values)
            values[field] = value
            with self.assertRaises(ValueError):
                edit_section(self.project,2,values)
            self.assertEqual(original,self.project.as_dict())

    def test_orbit_render(self):
        mesh = self.project.build()
        a = render_mesh(mesh,orbit_camera(0,20,13,100,80))
        b = render_mesh(mesh,orbit_camera(90,20,13,100,80))
        self.assertGreater(a.covered,0)
        self.assertGreater(b.covered,0)
        self.assertNotEqual(a.pixels,b.pixels)

    def test_bad_orbit(self):
        for args in ((0,90,13),(0,0,0),(float("nan"),0,13)):
            with self.assertRaises(ValueError):
                orbit_camera(*args)
