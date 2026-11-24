from pathlib import Path
import numpy as np, trimesh as tm, math,json
from scipy.interpolate import PchipInterpolator
import vtk
from vtk.util.numpy_support import numpy_to_vtk,numpy_to_vtkIdTypeArray,vtk_to_numpy
from PIL import Image
from trimesh.visual.material import PBRMaterial
from trimesh.visual.texture import TextureVisuals
P=Path(__file__).parent; O=P.parent; parts=[]
C={'silver':(182,185,189),'light':(205,208,212),'dark':(56,59,65),'roof':(69,72,78),'black':(30,32,35),'frame':(49,52,56),'steel':(107,110,114),'rubber':(25,27,29),'red':(195,26,24),'cream':(216,207,185),'lamp':(239,235,218),'rim':(130,132,134),'seam':(78,81,86)}
M={k:PBRMaterial(name=k,baseColorFactor=[*c,255],metallicFactor=.25,roughnessFactor=.5) for k,c in C.items()}
def add(n,m,c,g='body'):
 if isinstance(c,str):m.visual=TextureVisuals(material=M[c]); col=C[c]
 else:m.visual=c;col=None
 parts.append((n,m,col,g));return m
def bevel(s,r):
 s=np.array(s)/2;r=min(r,min(s)*.85);v=[]
 dirs=[np.array([np.sin(t)*np.cos(p),np.sin(t)*np.sin(p),np.cos(t)]) for t in np.linspace(0,np.pi/2,7) for p in np.linspace(0,np.pi/2,7)]
 for a in [-1,1]:
  for b in [-1,1]:
   for c in [-1,1]:
    for u in dirs:v.append(np.array([a,b,c])*(s-r+u*r))
 return tm.convex.convex_hull(np.unique(np.round(v,12),axis=0))
def box(n,p,s,c,r=.025,g='body'):
 m=bevel(s,r) if r else tm.creation.box(s);m.apply_translation(p);return add(n,m,c,g)
def cyl(n,p,r,l,c,axis=(0,0,1),N=24,g='body'):
 m=tm.creation.cylinder(radius=r,height=l,sections=max(32,N*2));m.apply_transform(tm.geometry.align_vectors([0,0,1],axis));m.apply_translation(p);return add(n,m,c,g)
def rod(n,a,b,r,c,g='body',square=False):
 a=np.array(a);b=np.array(b);d=b-a;m=bevel((r*2,r*2,np.linalg.norm(d)),r*.25) if square else tm.creation.cylinder(radius=r,height=np.linalg.norm(d),sections=48);m.apply_transform(tm.geometry.align_vectors([0,0,1],d));m.apply_translation((a+b)/2);return add(n,m,c,g)
# X width, +Y nose, Z up. Inferred art units, not real dimensions.
S=np.array([[-3.72,.62,2.30,.71],[-3.66,.76,2.40,.67],[-3.51,.85,2.45,.65],[-3.26,.88,2.47,.65],[-2.7,.88,2.48,.65],[-1.5,.88,2.48,.65],[0,.88,2.48,.65],[1.5,.88,2.48,.65],[2.25,.87,2.46,.65],[2.54,.84,2.40,.65],[2.82,.79,2.24,.65],[3.12,.70,1.95,.65],[3.39,.59,1.57,.66],[3.57,.51,1.30,.69],[3.67,.47,1.12,.72],[3.72,.42,1.04,.76]])
Q=np.array([[-.74,0],[-.94,.025],[-1,.09],[-1,.20],[-1,.37],[-1,.60],[-1,.78],[-.98,.86],[-.92,.92],[-.78,.97],[-.55,1],[0,1],[.55,1],[.78,.97],[.92,.92],[.98,.86],[1,.78],[1,.60],[1,.37],[1,.20],[1,.09],[.94,.025],[.74,0],[0,0],[-.74,0]])
S0=S.copy();Q0=Q.copy()
ys=np.concatenate([np.linspace(a,b,12 if a>=2.25 or b<=-2.7 else 6,endpoint=False) for a,b in zip(S0[:-1,0],S0[1:,0])]+[S0[-1:,0]])
S=np.column_stack([ys,PchipInterpolator(S0[:,0],S0[:,1:],axis=0)(ys)])
Q=PchipInterpolator(np.arange(len(Q0)),Q0,axis=0)(np.linspace(0,len(Q0)-1,(len(Q0)-1)*4+1))
v=[];uv=[];f=[];n=len(Q)
for y,w,z,b in S:
 for j,(x,h) in enumerate(Q):v.append((x*w,y,b+h*(z-b)));uv.append(((y+3.72)/7.44,j/(n-1)))
for i in range(len(S)-1):
 for j in range(n-1):
  a=i*n+j;b=a+1;c=a+n;d=c+1;f.extend([(a,b,c),(b,d,c)])
# actual UV livery texture, red band on paint, not extra mesh.
W,H=4096,2048; Y=np.linspace(-3.72,3.72,W)[None,:]; hh=np.interp(np.linspace(n-1,0,H),np.arange(n),Q[:,1])[:,None]; h=np.broadcast_to(hh,(H,W)); y=np.broadcast_to(Y,(H,W)); A=np.empty((H,W,3),np.uint8);A[:]=C['silver'];lo=.105+.035*np.clip((-y-1.15)/.65,0,1);hi=lo+.125+.035*np.maximum(y-2.45,0);A[(h>=lo)&(h<=hi)]=C['red'];A[h<.085]=C['dark'];A[(h>.78)&(h<=.92)]=C['dark'];A[h>.92]=C['roof'];A[(y>2.12)&(h>PchipInterpolator([2.12,2.54,3.12,3.72],[.88,.73,.56,.48])(np.clip(y,2.12,3.72)))]=C['dark'];
for seam_y in [-2.24,-.72,.35,1.53]:
 mask=(abs(y-seam_y)<.009)&(h>.25)&(h<.76);A[mask]=(A[mask].astype(np.float32)*.79).astype(np.uint8)
from PIL import ImageFilter
tex=Image.fromarray(A).filter(ImageFilter.GaussianBlur(.45));tex.save(P/'body_livery.png');mat=PBRMaterial(name='Painted body livery',baseColorTexture=tex,baseColorFactor=[255]*4,metallicFactor=.32,roughnessFactor=.45)
add('body_UV_livery',tm.Trimesh(v,f,process=False),TextureVisuals(uv=np.array(uv),material=mat))
for i,nm in [(0,'rear'),(-1,'nose')]:
 y,w,z,b=S[i];v=np.array([(x*w,y,b+h*(z-b)) for x,h in Q[:-1]]+[(0,y,(z+b)/2)]);ff=[(len(v)-1,j,(j+1)%(len(v)-1)) for j in range(len(v)-1)];m=tm.Trimesh(v,ff,process=False)
 if i==0:m.invert()
 add(nm+'_cap',m,'dark')
box('underframe',(0,0,.69),(1.63,7.35,.25),'frame',.06)
for s,nm in [(1,'front'),(-1,'rear')]:
 box(nm+'_bufferbeam',(0,s*3.77,.68),(1.46,.38,.38),'black',.075);box(nm+'_coupler_shank',(0,s*4.03,.51),(.25,.42,.22),'frame');box(nm+'_coupler_head',(0,s*4.26,.51),(.39,.23,.32),'black',.035)
 for x in [-.57,.57]:box(nm+f'_buffer{x}',(x,s*3.92,.78),(.27,.26,.23),'steel')
for x in [-.25,0,.25]:
 for nm,dy,sz,co in [('housing',0,(.226,.075,.18),'black'),('lens',.045,(.186,.04,.135),'lamp')]:
  m=bevel(sz,.012);m.apply_transform(tm.transformations.rotation_matrix(math.radians(-22),[1,0,0]));m.apply_translation((x,3.675+dy,1.04));add(f'headlamp_{nm}{x}',m,co)
for sg in [-1,1]:
 s='L' if sg<0 else 'R'
 for y0 in [2.05,-2.78]:
  box(f'{s}_door_border{y0}',(sg*.882,y0,1.43),(.046,.70,.66),'seam');box(f'{s}_door{y0}',(sg*.909,y0,1.43),(.045,.655,.615),'silver');box(f'{s}_handle{y0}',(sg*.943,y0+.19,1.43),(.047,.055,.15),'black',.016)
 for k,y0 in enumerate([.82,-1.63]):
  box(f'{s}_vent{k}',(sg*.884,y0,1.85),(.07,1.05,.46),'black',.045);box(f'{s}_vent_recess{k}',(sg*.925,y0,1.85),(.035,.95,.37),'rubber')
  for j in range(11):box(f'{s}_vent{k}_slat{j}',(sg*.957,y0-.43+j*.086,1.85),(.075,.045,.345),'steel',.014)
  for j in range(6):box(f'{s}_smallvent{k}_{j}',(sg*.886,y0-.26+j*.09,2.15),(.035,.052,.115),'seam',.009)
 for k,y0 in enumerate([1.53,.35,-.72,-2.24]):
  box(f'{s}_seam{k}',(sg*.883,y0,1.42),(.012,.018,.54),'seam',.003)
  for z0 in [1.08,2.22]:cyl(f'{s}_fastener{k}_{z0}',(sg*.895,y0,z0),.023,.013,'steel',(1,0,0),12)
 for k,y0 in enumerate([0,-.89,.91]):box(f'{s}_underbox{k}',(sg*.76,y0,.45),(.32,.65,.38),'frame',.035);box(f'{s}_underbox_face{k}',(sg*.94,y0,.45),(.07,.58,.29),'steel',.018)
# Additional door hinges, fasteners, equipment cabinets and lamp surround.
for sg in [-1,1]:
 s='L' if sg<0 else 'R'
 for yy in [2.05,-2.78]:
  for dz in [-.22,.22]:box(f'{s}_hinge{yy}_{dz}',(sg*.942,yy-.282,1.43+dz),(.026,.068,.083),'steel',.008)
  for dy in [-.27,.27]:
   for dz in [-.245,.245]:cyl(f'{s}_doorbolt{yy}_{dy}_{dz}',(sg*.935,yy+dy,1.43+dz),.012,.015,'steel',(1,0,0),12)
 for yy in [0,-.89,.91]:
  for dy in [-.24,.24]:
   for dz in [-.10,.10]:cyl(f'{s}_cabinetbolt{yy}_{dy}_{dz}',(sg*.981,yy+dy,.45+dz),.017,.018,'frame',(1,0,0),12)
  box(f'{s}_cabinet_latch{yy}',(sg*.98,yy,.47),(.035,.075,.065),'black',.008)
 for yy in [-2.98,-1.97,-.50,.56,1.74,2.31]:
  cyl(f'{s}_roof_seam_rivet{yy}',(sg*.848,yy,2.29),.016,.016,'steel',(1,0,0),12)
for nm,yy,zz,sz,co in [('outer',3.661,1.042,(.835,.07,.245),'steel'),('inner',3.697,1.045,(.774,.048,.205),'black')]:
 m=bevel(sz,.018);m.apply_transform(tm.transformations.rotation_matrix(math.radians(-22),[1,0,0]));m.apply_translation((0,yy,zz));add('lamp_bezel_'+nm,m,co)
for k,cy in enumerate([2.3,-2.38]):
 g=f'bogie{k}';box(g+'_center',(0,cy,.43),(1.32,1.72,.32),'black',.045,g)
 for j,y0 in enumerate([cy-.57,cy+.57]):
  cyl(g+f'_axle{j}',(0,y0,.36),.10,1.62,'steel',(1,0,0),20,g)
  for sg in [-1,1]:
   pre=f'b{k}_w{j}_{sg}'
   for nm,x,r,l,co in [('flange',.70,.345,.115,'black'),('tread',.77,.317,.17,'rubber'),('rim',.866,.277,.045,'steel'),('disc',.895,.235,.035,'frame'),('hub',.927,.102,.09,'rim')]:cyl(pre+'_'+nm,(sg*x,y0,.36),r,l,co,(1,0,0),64,g)
   for h0 in range(6):
    t=h0*math.pi/3;cyl(pre+f'_bolt{h0}',(sg*.924,y0+.15*math.cos(t),.36+.15*math.sin(t)),.026,.028,'steel',(1,0,0),10,g)
 for sg in [-1,1]:
  box(g+f'_sideframe{sg}',(sg*.91,cy,.48),(.17,1.66,.20),'frame',.045,g)
  for y0 in [cy-.57,cy+.57]:box(g+f'_bearing{sg}_{y0}',(sg*1.01,y0,.48),(.15,.34,.29),'steel',.045,g);cyl(g+f'_bearingcap{sg}_{y0}',(sg*1.10,y0,.48),.12,.05,'frame',(1,0,0),24,g)
  for yy in [cy-.57,cy+.57]:
   for dz in [-.09,.09]:cyl(f'{g}_bearing_bolt{sg}_{yy}_{dz}',(sg*1.103,yy+.09,.48+dz),.019,.023,'steel',(1,0,0),12,g)
   rod(f'{g}_damper{sg}_{yy}',(sg*1.025,yy,.50),(sg*1.025,yy+(.20 if yy<cy else -.20),.68),.045,'steel',g)
  for yy in [cy-.24,cy+.24]:box(f'{g}_frame_bracket{sg}_{yy}',(sg*1.008,yy,.44),(.065,.13,.22),'steel',.015,g)
  for y0 in [cy-.28,cy+.28]:
   cyl(g+f'_spring{sg}_{y0}',(sg*.96,y0,.62),.078,.19,'black',N=16,g=g)
   for z0 in [.55,.59,.63,.67]:cyl(g+f'_springring{sg}_{y0}_{z0}',(sg*.96,y0,z0),.085,.019,'steel',N=16,g=g)
# Keep all four forward hatch bases on the roof, clear of the nose slope.
for x in [-.34,.34]:
 for y0 in [1.62,2.08]:
  z=2.455
  box(f'roof_hatch_base{x}_{y0}',(x,y0,z),(.55,.40,.105),'dark',.025)
  box(f'roof_hatch_gasket{x}_{y0}',(x,y0,z+.054),(.50,.35,.027),'steel',.018)
  box(f'roof_hatch{x}_{y0}',(x,y0,z+.11),(.46,.32,.10),'light',.025)
  for dx in [-.235,.235]:
   for dy in [-.159,.159]:cyl(f'roof_hatch_bolt{x}_{y0}_{dx}_{dy}',(x+dx,y0+dy,z+.065),.019,.018,'steel',N=16)

for x in [-.34,.34]:box(f'rear_hatch_base{x}',(x,-2.88,2.49),(.55,.54,.09),'dark');box(f'rear_hatch{x}',(x,-2.88,2.56),(.47,.45,.10),'light',.04)
box('radiator_plinth',(0,.40,2.53),(1.39,1.47,.18),'dark',.04);box('radiator_core',(0,.40,2.65),(1.26,1.33,.11),'black')
for i in range(17):box(f'radiator_fin{i}',(0,-.22+i*.078,2.735),(1.21,.049,.095),'dark',.009)
# Reference roof trim, radiator rails and mounting bolts.
for sg in [-1,1]:
 box(f'radiator_edge{sg}',(sg*.64,.40,2.715),(.045,1.32,.06),'steel',.012)
 for yy in [-.27,1.07]:cyl(f'radiator_bolt{sg}_{yy}',(sg*.64,yy,2.754),.023,.018,'steel',N=16)
 pts=[(sg*.79,-2.44,2.425),(sg*.79,-3.22,2.42),(sg*.73,-3.50,2.405),(sg*.60,-3.65,2.36),(sg*.42,-3.70,2.32),(0,-3.72,2.30)]
 for i,(a,b) in enumerate(zip(pts,pts[1:])):rod(f'rear_roof_trim{sg}_{i}',a,b,.024,'light')
for sg in [-1,1]:box(f'roof_rail{sg}',(sg*.73,-1.48,2.49),(.06,1.77,.075),'steel',.014)
g='pantograph';box('panto_plinth',(0,-1.65,2.54),(1.27,1.42,.13),'dark',.045,g)
for x in [-.43,.43]:
 for y0 in [-2.10,-1.21]:
  cyl(f'iso_base{x}_{y0}',(x,y0,2.65),.13,.07,'black',g=g);cyl(f'iso_core{x}_{y0}',(x,y0,2.78),.078,.25,'cream',g=g)
  for j in range(4):cyl(f'iso_rib{x}_{y0}_{j}',(x,y0,2.68+j*.061),.14-j*.008,.034,'cream',g=g)
  cyl(f'iso_cap{x}_{y0}',(x,y0,2.93),.09,.055,'steel',g=g)
box('panto_deck',(0,-1.65,2.96),(1.12,1.20,.12),'black',.025,g)
for x in [-.30,.30]:
 a=(x,-1.14,3.02);b=(x,-2.01,3.73);c=(x,-1.37,4.37);rod(f'panto_lower{x}',a,b,.069,'red',g,True);rod(f'panto_upper{x}',b,c,.059,'red',g,True)
 for k,p in enumerate([a,b,c]):cyl(f'panto_joint{x}_{k}',p,.101,.19,'steel',(1,0,0),20,g)
rod('panto_mid_cross',(-.37,-2.01,3.73),(.37,-2.01,3.73),.055,'black',g);rod('panto_upper_cross',(-.4,-1.37,4.37),(.4,-1.37,4.37),.055,'steel',g)
for y0 in [-1.51,-1.25]:
 box(f'contact_strip{y0}',(0,y0,4.43),(1.75,.115,.085),'black',.022,g)
 for sg in [-1,1]:rod(f'contact_end{sg}_{y0}',(sg*.84,y0,4.43),(sg*.95,y0,4.37),.044,'steel',g,True)
# Refine relative silhouette against reference views; dimensions remain inferred.
for name,m,col,g in parts:
    vv=m.vertices.copy()
    if g=='pantograph': vv[:,2]=2.48+(vv[:,2]-2.48)*.61
    if g.startswith('bogie'): vv[:,0]*=.87
    if name.startswith('rear_coupler'): vv[:,1]+=.30
    if name.startswith('front_coupler'): vv[:,1]-=.12
    vv[:,0]*=.96;vv[:,2]*=.91
    m.vertices=vv
# Explicit exported vertex normals; preserve hard edges and UVs.
def with_normals(m,name):
 pts=vtk.vtkPoints();pts.SetData(numpy_to_vtk(np.ascontiguousarray(m.vertices),deep=True))
 cells=vtk.vtkCellArray();ids=np.column_stack((np.full(len(m.faces),3),m.faces)).astype(np.int64)
 cells.SetCells(len(ids),numpy_to_vtkIdTypeArray(ids.ravel(),deep=True))
 poly=vtk.vtkPolyData();poly.SetPoints(pts);poly.SetPolys(cells)
 has_uv=getattr(m.visual,'uv',None) is not None
 if has_uv:
  tc=numpy_to_vtk(np.asarray(m.visual.uv,dtype=np.float32),deep=True);tc.SetNumberOfComponents(2);poly.GetPointData().SetTCoords(tc)
 normal=vtk.vtkPolyDataNormals();normal.SetInputData(poly);normal.ConsistencyOn();normal.AutoOrientNormalsOff();normal.SplittingOn();normal.SetFeatureAngle(45);normal.ComputePointNormalsOn();normal.Update();o=normal.GetOutput()
 v=vtk_to_numpy(o.GetPoints().GetData()).copy();f=vtk_to_numpy(o.GetPolys().GetData()).reshape(-1,4)[:,1:].copy();n=vtk_to_numpy(o.GetPointData().GetNormals()).copy()
 if name=='body_UV_livery':
  _,inv=np.unique(np.round(v,9),axis=0,return_inverse=True);sums=np.zeros((inv.max()+1,3));np.add.at(sums,inv,n);norm=np.linalg.norm(sums,axis=1);n=sums[inv]/np.maximum(norm[inv,None],1e-12)
 vis=TextureVisuals(uv=vtk_to_numpy(o.GetPointData().GetTCoords()).copy() if has_uv else None,material=m.visual.material)
 return tm.Trimesh(v,f,visual=vis,vertex_normals=n,process=False)
parts=[(name,with_normals(m,name),col,g) for name,m,col,g in parts]
T=tm.transformations.rotation_matrix(-math.pi/2,[1,0,0]);stats={}
for fn,inc in [('Locomotive_v3.glb',lambda g:True),('Locomotive_v3_body.glb',lambda g:g!='pantograph'),('Locomotive_v3_pantograph.glb',lambda g:g=='pantograph')]:
 sc=tm.Scene()
 for name,m,col,g in parts:
  if inc(g):mm=m.copy();mm.apply_transform(T);sc.add_geometry(mm,geom_name=name,node_name=name)
 (O/fn).write_bytes(sc.export(file_type='glb',include_normals=True));re=tm.load(O/fn,force='scene',process=False);stats[fn]={'meshes':len(re.geometry),'triangles':sum(len(m.faces) for m in re.geometry.values()),'bounds':re.bounds.tolist()};print(fn,stats[fn],flush=True)
(P/'metrics.json').write_text(json.dumps(stats,indent=2))
# real geometry rendering
import vtk
from vtk.util.numpy_support import numpy_to_vtk,numpy_to_vtkIdTypeArray
ren=vtk.vtkRenderer();ren.SetBackground(.93,.94,.955);ren.SetBackground2(.76,.79,.83);ren.GradientBackgroundOn();win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetMultiSamples(8);win.AddRenderer(ren)
for name,m,col,g in parts:
 pts=vtk.vtkPoints();pts.SetData(numpy_to_vtk(np.ascontiguousarray(m.vertices),deep=True));cells=vtk.vtkCellArray();ids=np.column_stack((np.full(len(m.faces),3),m.faces)).astype(np.int64);cells.SetCells(len(ids),numpy_to_vtkIdTypeArray(ids.ravel(),deep=True));poly=vtk.vtkPolyData();poly.SetPoints(pts);poly.SetPolys(cells)
 if col is None:
  tc=numpy_to_vtk(np.asarray(m.visual.uv,dtype=np.float32),deep=True);tc.SetNumberOfComponents(2);poly.GetPointData().SetTCoords(tc)
 nn=numpy_to_vtk(np.asarray(m.vertex_normals,dtype=np.float32),deep=True);nn.SetNumberOfComponents(3);poly.GetPointData().SetNormals(nn);mapper=vtk.vtkPolyDataMapper();mapper.SetInputData(poly);act=vtk.vtkActor();act.SetMapper(mapper);prop=act.GetProperty();prop.SetInterpolationToPhong();prop.SetAmbient(.33);prop.SetDiffuse(.68);prop.SetSpecular(.22);prop.SetSpecularPower(24)
 if col is None:
  rd=vtk.vtkPNGReader();rd.SetFileName(str(P/'body_livery.png'));tx=vtk.vtkTexture();tx.SetInputConnection(rd.GetOutputPort());tx.InterpolateOn();act.SetTexture(tx);prop.SetColor(1,1,1)
 else:prop.SetColor(*(np.array(col)/255))
 ren.AddActor(act)
ren.AutomaticLightCreationOff()
for pos,intensity in [((-7,7,12),.9),((5,-6,7),.55),((2,6,3),.23)]:
 l=vtk.vtkLight();l.SetLightTypeToSceneLight();l.SetPosition(*pos);l.SetFocalPoint(0,0,1);l.SetIntensity(intensity);ren.AddLight(l)
cam=ren.GetActiveCamera();cam.ParallelProjectionOn()
for name,pos,up,scale,size,target in [('hero',(-11,10,8),(0,0,1),2.95,(2400,1600),(0,0,1.70)),('side',(-15,0,2.05),(0,0,1),2.55,(2400,1300),(0,0,1.65)),('top',(0,0,20),(1,0,0),2.6,(2400,1300),(0,0,1.7)),('front',(0,15,2.1),(0,0,1),2.55,(1200,1440),(0,0,1.65)),('rear',(0,-15,2.1),(0,0,1),2.55,(1200,1440),(0,0,2.1))]:
 win.SetSize(*size);cam.SetPosition(*pos);cam.SetFocalPoint(*target);cam.SetViewUp(*up);cam.SetParallelScale(scale);ren.ResetCameraClippingRange();win.Render();im=vtk.vtkWindowToImageFilter();im.SetInput(win);im.ReadFrontBufferOff();im.Update();wr=vtk.vtkPNGWriter();wr.SetFileName(str(P/f'{name}.png'));wr.SetInputConnection(im.GetOutputPort());wr.Write();print('render',name,flush=True)
win.Finalize()
