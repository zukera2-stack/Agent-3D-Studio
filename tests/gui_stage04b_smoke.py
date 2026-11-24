"""Real Tk smoke test under Xvfb; run from repo root: python -m tests.gui_stage04b_smoke
Also runnable via python tests/gui_stage04b_smoke.py with PYTHONPATH=.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from a3ds import linked_editor
from a3ds.project import SurfaceProject, demo_project
from a3ds.glb import read_glb
from a3ds.camera import standard_views

def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)

def main():
    with tempfile.TemporaryDirectory() as tmp:
        project_path = Path(tmp) / "edited.a3ds.json"
        glb_path = Path(tmp) / "edited.glb"
        errors = []
        dialogs = []
        def exercise(root, *args, **kwargs):
            try:
                root.update()
                children = list(descendants(root))
                canvases = [c for c in children if isinstance(c, tk.Canvas)]
                assert len(canvases) == 4, len(canvases)
                buttons = {c.cget("text"): c for c in children if isinstance(c, ttk.Button)}
                side = canvases[1]
                camera = standard_views(420, 300)["side"]
                i,k,x,y = next(p for p in linked_editor.handles(demo_project(), camera, "side") if p[:2] == (3,"center"))
                x,y = round(x),round(y)
                def images():
                    return [c.itemcget(c.find_all()[0],"image") for c in canvases]
                initial = images()
                side.event_generate("<Button-1>",x=x,y=y)
                side.event_generate("<B1-Motion>",x=x+8,y=y-5)
                side.event_generate("<ButtonRelease-1>",x=x+8,y=y-5)
                root.update()
                assert images() != initial
                buttons["Save"].invoke()
                edited = SurfaceProject.load(project_path)
                assert edited.sections[3].y > demo_project().sections[3].y
                assert edited.sections[3].center_z > demo_project().sections[3].center_z
                buttons["Undo"].invoke()
                buttons["Save"].invoke()
                assert SurfaceProject.load(project_path).as_dict() == demo_project().as_dict()
                buttons["Redo"].invoke()
                buttons["Save"].invoke()
                assert SurfaceProject.load(project_path).as_dict() == edited.as_dict()
                buttons["GLB"].invoke()
                assert read_glb(glb_path).validate(require_closed=True, require_outward=True).ok
                hero = canvases[3]
                old = images()[3]
                hero.event_generate("<Button-1>",x=180,y=140)
                hero.event_generate("<B1-Motion>",x=205,y=150)
                hero.event_generate("<ButtonRelease-1>",x=205,y=150)
                root.update()
                assert images()[3] != old
                assert not dialogs, dialogs
                print("GUI_SMOKE PASS: four canvases, mouse drag, save, undo/redo, GLB and orbit")
            except BaseException as exc:
                errors.append(exc)
            finally:
                root.destroy()
        def save_dialog(**kwargs):
            return str(glb_path if kwargs.get("defaultextension")==".glb" else project_path)
        with patch.object(tk.Tk,"mainloop",exercise), patch.object(filedialog,"asksaveasfilename",save_dialog), patch.object(messagebox,"showerror",lambda *a,**k:dialogs.append(a)):
            linked_editor.main()
        if errors:
            raise errors[0]

if __name__ == "__main__":
    main()
