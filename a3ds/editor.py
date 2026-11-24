"""Stage 04: local Tk editor; geometry and rendering remain in A3DS.
Run python -m a3ds.editor. No Tk import until the GUI is launched.
"""
from dataclasses import replace
from math import cos, sin, radians, isfinite
from pathlib import Path
import base64

from .camera import Camera, standard_views
from .math3d import Vec3
from .project import SurfaceProject, demo_project
from .raster import render_mesh
from .png import encode_png
from .glb import write_glb

FIELDS = ("y", "center_z", "half_width", "half_height", "exponent")


def edit_section(project, index, values):
    """Transactional edit: validate a fresh candidate before replacing state."""
    if not 0 <= index < len(project.sections):
        raise ValueError("Invalid section index")
    if set(values) != set(FIELDS):
        raise ValueError("Expected all section fields")
    sections = list(project.sections)
    sections[index] = replace(sections[index], **{k: float(v) for k, v in values.items()})
    candidate = replace(project, sections=sections)
    report = candidate.build().validate(require_closed=True, require_outward=True)
    if not report.ok:
        raise ValueError(str(report.errors))
    return candidate


def orbit_camera(yaw, pitch, distance, width=480, height=360):
    if not all(isfinite(v) for v in (yaw, pitch, distance)):
        raise ValueError("Nonfinite orbit")
    if not -89 <= pitch <= 89 or not 2 <= distance <= 60:
        raise ValueError("Orbit outside bounds")
    a, b = radians(yaw), radians(pitch)
    target = Vec3(0, 0, 1.15)
    pos = target + Vec3(distance*cos(b)*cos(a), distance*cos(b)*sin(a), distance*sin(b))
    return Camera(width, height, pos, target, Vec3(0,0,1),
                  projection="perspective", fov_y_degrees=52, far=100)


def main():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    root = tk.Tk()
    root.title("Agent 3D Studio | Stage 04")
    project = demo_project()
    history = []
    view = tk.StringVar(value="hero")
    yaw = tk.DoubleVar(value=48)
    pitch = tk.DoubleVar(value=24)
    distance = tk.DoubleVar(value=13)
    status = tk.StringVar()
    dirty = False
    photo = None
    pending = None
    drag = None
    toolbar = ttk.Frame(root, padding=8)
    toolbar.pack(fill="x")
    work = ttk.Frame(root, padding=8)
    work.pack(fill="both", expand=True)
    panel = ttk.Frame(work)
    panel.pack(side="right", fill="y")
    canvas = tk.Label(work, bg="#202631")
    canvas.pack(side="left", fill="both", expand=True)
    sections = tk.Listbox(panel, height=12, exportselection=False)
    sections.pack(fill="x")
    fields = {k: tk.StringVar() for k in FIELDS}
    for k, var in fields.items():
        ttk.Label(panel, text=k + " (BU)" if k != "exponent" else k).pack(anchor="w")
        ttk.Entry(panel, textvariable=var).pack(fill="x")
    ttk.Label(root, textvariable=status, padding=6).pack(fill="x")

    def error(exc):
        messagebox.showerror("A3DS", str(exc))

    def refresh():
        nonlocal photo, pending
        pending = None
        try:
            mesh = project.build()
            camera = (orbit_camera(yaw.get(), pitch.get(), distance.get())
                      if view.get() == "hero" else
                      standard_views(480,360)[view.get()])
            if view.get() != "hero":
                camera = replace(camera, vertical_span=camera.vertical_span*distance.get()/13)
            render = render_mesh(mesh, camera, background=(32,38,49))
            photo = tk.PhotoImage(data=base64.b64encode(
                encode_png(render.width, render.height, render.pixels)).decode("ascii"))
            canvas.configure(image=photo)
            status.set(f"{project.name} | {len(mesh.vertices)} vertices | {len(mesh.triangles)} triangles | BU")
        except (ValueError, TypeError) as exc:
            error(exc)

    def schedule(*_):
        nonlocal pending
        if pending is not None:
            root.after_cancel(pending)
        pending = root.after(100, refresh)

    def selected(*_):
        sel = sections.curselection()
        if sel:
            item = project.sections[sel[0]]
            for k,var in fields.items():
                var.set(str(getattr(item,k)))

    def populate(index=0):
        sections.delete(0,"end")
        for i,s in enumerate(project.sections):
            sections.insert("end", f"{i+1}: Y={s.y:.3f}")
        sections.selection_set(min(index,len(project.sections)-1))
        selected()
        schedule()

    def apply():
        nonlocal project, dirty
        sel = sections.curselection()
        if not sel:
            return
        try:
            candidate = edit_section(project,sel[0],{k:v.get() for k,v in fields.items()})
        except (ValueError,TypeError) as exc:
            error(exc)
            return
        history.append(project)
        project = candidate
        dirty = True
        populate(sel[0])

    def undo():
        nonlocal project, dirty
        if history:
            project = history.pop()
            dirty = True
            populate()

    def discard_ok():
        return not dirty or messagebox.askyesno("A3DS","Discard unsaved project changes?")

    def load():
        nonlocal project, dirty
        if not discard_ok():
            return
        path = filedialog.askopenfilename(filetypes=[("A3DS project","*.json")])
        if not path:
            return
        try:
            candidate = SurfaceProject.load(path)
            report = candidate.build().validate(require_closed=True,require_outward=True)
            if not report.ok:
                raise ValueError(str(report.errors))
            project = candidate
            history.clear()
            dirty = False
            populate()
        except (OSError,ValueError,TypeError,KeyError) as exc:
            error(exc)

    def save():
        nonlocal dirty
        path = filedialog.asksaveasfilename(defaultextension=".a3ds.json")
        if path:
            try:
                project.save(path)
                dirty = False
            except OSError as exc:
                error(exc)

    def export():
        path = filedialog.asksaveasfilename(defaultextension=".glb")
        if path:
            try:
                write_glb(project.build(),Path(path))
            except (OSError,ValueError) as exc:
                error(exc)

    def start_drag(event):
        nonlocal drag
        drag = (event.x,event.y)

    def move_drag(event):
        nonlocal drag
        if drag and view.get()=="hero":
            yaw.set((yaw.get()+(event.x-drag[0])*0.5)%360)
            pitch.set(max(-89,min(89,pitch.get()+(event.y-drag[1])*0.5)))
            drag=(event.x,event.y)
            schedule()

    def zoom(event):
        sign = 1 if event.delta > 0 or getattr(event,"num",None)==4 else -1
        distance.set(max(2,min(60,distance.get()*(0.9 if sign>0 else 1.1))))
        schedule()

    for name,cmd in (("Open",load),("Save as",save),("Export GLB",export),("Undo",undo)):
        ttk.Button(toolbar,text=name,command=cmd).pack(side="left")
    for name in ("hero","front","side","top","rear"):
        ttk.Radiobutton(toolbar,text=name,value=name,variable=view,command=schedule).pack(side="left")
    ttk.Button(panel,text="Apply section",command=apply).pack(fill="x",pady=6)
    sections.bind("<<ListboxSelect>>",selected)
    canvas.bind("<Button-1>",start_drag)
    canvas.bind("<B1-Motion>",move_drag)
    for event in ("<MouseWheel>","<Button-4>","<Button-5>"):
        canvas.bind(event,zoom)
    root.protocol("WM_DELETE_WINDOW",lambda: root.destroy() if discard_ok() else None)
    populate()
    root.mainloop()


if __name__ == "__main__":
    main()
