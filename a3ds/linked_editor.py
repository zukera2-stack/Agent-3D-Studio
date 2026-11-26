"""Four native A3DS viewports, orthographic section handles and shared edit history.
Run python -m a3ds.linked_editor. Tk is only a display/input layer.
"""
from dataclasses import replace
from math import isfinite
from .editor import edit_section, orbit_camera, FIELDS
from .project import demo_project, SurfaceProject
from .camera import standard_views
from .math3d import Vec3
from .raster import render_mesh
from .png import encode_png
from .glb import write_glb
import base64


class Session:
    def __init__(self, project):
        self.project = project
        self.history = []
        self.future = []

    def apply(self, index, values):
        candidate = edit_section(self.project, index, values)
        if candidate.as_dict() != self.project.as_dict():
            self.history.append(self.project)
            self.project = candidate
            self.future.clear()

    def undo(self):
        if self.history:
            self.future.append(self.project)
            self.project = self.history.pop()

    def redo(self):
        if self.future:
            self.history.append(self.project)
            self.project = self.future.pop()


def handles(project, camera, view):
    """Return visible screen handles with stable (section index, kind) identity.
    Side: center and upper edge. Top: center and positive-X edge.
    Front: only the foremost section, avoiding ambiguous overlapping handles.
    """
    if view not in ("side","top","front"):
        return []
    result = []
    indices = [len(project.sections)-1] if view == "front" else range(len(project.sections))
    for i in indices:
        s = project.sections[i]
        points = {"center": Vec3(0,s.y,s.center_z)}
        if view in ("side","front"):
            points["height"] = Vec3(0,s.y,s.center_z+s.half_height)
        if view in ("top","front"):
            points["width"] = Vec3(s.half_width,s.y,s.center_z)
        for kind,p in points.items():
            q = camera.project(p)
            if q is not None:
                result.append((i,kind,q.x,q.y))
    return result


def drag_values(section, camera, view, kind, dx, dy):
    """Invert orthographic screen displacement using the actual camera basis."""
    if camera.projection != "orthographic" or not all(isfinite(v) for v in (dx,dy)):
        raise ValueError("Invalid orthographic drag")
    right,up,_ = camera.basis()
    d = right*(dx/camera.pixels_per_unit) + up*(-dy/camera.pixels_per_unit)
    values = {k:getattr(section,k) for k in FIELDS}
    if kind == "center" and view in ("side","top","front"):
        if view in ("side","top"):
            values["y"] += d.y
        if view in ("side","front"):
            values["center_z"] += d.z
    elif kind == "height" and view in ("side","front"):
        values["half_height"] += d.z
    elif kind == "width" and view in ("top","front"):
        values["half_width"] += d.x
    else:
        raise ValueError("Unsupported handle")
    return values


def main():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    root=tk.Tk()
    root.title("Agent 3D Studio | Stage 04B")
    root.geometry("1000x780")
    session=Session(demo_project())
    saved=session.project.as_dict()
    w,h=420,300
    views=("front","side","top","hero")
    canvases={}
    photos={}
    references={}
    cameras={}
    drag=None
    yaw,pitch,distance=48.,24.,13.
    grid=tk.BooleanVar(value=True)
    status=tk.StringVar(value="BU | drag section handles")
    toolbar=ttk.Frame(root)
    toolbar.pack(fill="x")
    area=ttk.Frame(root)
    area.pack(fill="both",expand=True)
    for i,view in enumerate(views):
        frame=ttk.LabelFrame(area,text=view)
        frame.grid(row=i//2,column=i%2,sticky="nsew")
        c=tk.Canvas(frame,width=w,height=h,bg="#202631",highlightthickness=0)
        c.pack(expand=True)
        canvases[view]=c
    for i in range(2):
        area.rowconfigure(i,weight=1)
        area.columnconfigure(i,weight=1)
    ttk.Label(root,textvariable=status).pack(fill="x")

    def refresh():
        mesh=session.project.build()
        cameras.update(standard_views(w,h))
        cameras["hero"]=orbit_camera(yaw,pitch,distance,w,h)
        for view,c in canvases.items():
            cam=cameras[view]
            r=render_mesh(mesh,cam,background=(32,38,49))
            photos[view]=tk.PhotoImage(data=base64.b64encode(encode_png(w,h,r.pixels)).decode("ascii"))
            c.delete("all")
            c.create_image(0,0,image=photos[view],anchor="nw")
            # Reference is a manually aligned screen-space overlay, not calibration.
            if view in references:
                c.create_image(0,0,image=references[view],anchor="nw")
            if grid.get() and view!="hero":
                step=cam.pixels_per_unit
                origin=cam.project(Vec3(0,0,0))
                if origin:
                    x=origin.x%step
                    while x<w:
                        c.create_line(x,0,x,h,fill="#526070",dash=(2,5))
                        x+=step
                    y=origin.y%step
                    while y<h:
                        c.create_line(0,y,w,y,fill="#526070",dash=(2,5))
                        y+=step
            for i,kind,x,y in handles(session.project,cam,view):
                color={"center":"#f2bc63","width":"#60d5ec","height":"#7de0a0"}[kind]
                c.create_oval(x-4,y-4,x+4,y+4,fill=color,outline="#151a20")
        status.set(f"BU | {len(mesh.vertices)} vertices | {len(session.history)} edits | {len(session.future)} redo")

    def press(view,event):
        nonlocal drag
        if view=="hero":
            drag=(view,event.x,event.y,None,None)
            return
        options=handles(session.project,cameras[view],view)
        if options:
            i,k,x,y=min(options,key=lambda p:(p[2]-event.x)**2+(p[3]-event.y)**2)
            if (x-event.x)**2+(y-event.y)**2<=100:
                drag=(view,event.x,event.y,i,k)

    def motion(view,event):
        nonlocal yaw,pitch,drag
        if drag is None or drag[0]!=view:
            return
        if view=="hero":
            yaw=(yaw+(event.x-drag[1])*.5)%360
            pitch=max(-89,min(89,pitch+(event.y-drag[2])*.5))
            drag=(view,event.x,event.y,None,None)
            refresh()
        else:
            c=canvases[view]
            c.delete("ghost")
            c.create_oval(event.x-5,event.y-5,event.x+5,event.y+5,outline="white",tags="ghost")

    def release(view,event):
        nonlocal drag
        if drag is None or drag[0]!=view:
            return
        _,x,y,i,k=drag
        drag=None
        if i is not None:
            try:
                session.apply(i,drag_values(session.project.sections[i],cameras[view],view,k,event.x-x,event.y-y))
            except (ValueError,TypeError) as exc:
                messagebox.showerror("Rejected edit",str(exc))
            refresh()

    def zoom(event):
        nonlocal distance
        sign=1 if event.delta>0 or getattr(event,"num",None)==4 else -1
        distance=max(2,min(60,distance*(.9 if sign>0 else 1.1)))
        refresh()

    def discard_ok():
        return session.project.as_dict()==saved or messagebox.askyesno("A3DS","Discard unsaved geometry edits?")

    def open_project():
        nonlocal session,saved
        if not discard_ok():
            return
        p=filedialog.askopenfilename(filetypes=[("A3DS JSON","*.json")])
        if p:
            try:
                model=SurfaceProject.load(p)
                report=model.build().validate(require_closed=True,require_outward=True)
                if not report.ok:
                    raise ValueError(str(report.errors))
                session=Session(model)
                saved=model.as_dict()
                references.clear()
                refresh()
            except (OSError,ValueError,TypeError,KeyError) as exc:
                messagebox.showerror("A3DS",str(exc))

    def save():
        nonlocal saved
        p=filedialog.asksaveasfilename(defaultextension=".a3ds.json")
        if p:
            try:
                session.project.save(p)
                saved=session.project.as_dict()
            except OSError as exc:
                messagebox.showerror("A3DS",str(exc))

    def export():
        p=filedialog.asksaveasfilename(defaultextension=".glb")
        if p:
            try:
                write_glb(session.project.build(),p)
            except (OSError,ValueError) as exc:
                messagebox.showerror("A3DS",str(exc))

    def reference(view):
        p=filedialog.askopenfilename(filetypes=[("PNG overlay","*.png")])
        if p:
            try:
                im=tk.PhotoImage(file=p)
                if (im.width(),im.height())!=(w,h):
                    raise ValueError(f"Use prealigned transparent PNG {w}x{h}")
                references[view]=im
                refresh()
            except (ValueError,tk.TclError) as exc:
                messagebox.showerror("Reference",str(exc))

    for label,cmd in (("Open",open_project),("Save",save),("GLB",export),
                      ("Undo",lambda:(session.undo(),refresh())),
                      ("Redo",lambda:(session.redo(),refresh())),
                      ("Clear overlays",lambda:(references.clear(),refresh()))):
        ttk.Button(toolbar,text=label,command=cmd).pack(side="left")
    ttk.Checkbutton(toolbar,text="1 BU grid",variable=grid,command=refresh).pack(side="left")
    for view,c in canvases.items():
        c.bind("<Button-1>",lambda e,v=view:press(v,e))
        c.bind("<B1-Motion>",lambda e,v=view:motion(v,e))
        c.bind("<ButtonRelease-1>",lambda e,v=view:release(v,e))
        if view!="hero":
            c.bind("<Button-3>",lambda e,v=view:reference(v))
        else:
            for event in ("<MouseWheel>","<Button-4>","<Button-5>"):
                c.bind(event,zoom)
    root.protocol("WM_DELETE_WINDOW",lambda:root.destroy() if discard_ok() else None)
    refresh()
    root.mainloop()


if __name__=="__main__":
    main()
