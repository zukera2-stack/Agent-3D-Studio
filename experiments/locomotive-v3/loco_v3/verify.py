from pathlib import Path
import json,hashlib,numpy as np,trimesh as tm
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).parent;O=P.parent
report={}
for fname in ['Locomotive_v3.glb','Locomotive_v3_body.glb','Locomotive_v3_pantograph.glb']:
 p=O/fname;s=tm.load(p,force='scene',process=False)
 assert all(np.isfinite(m.vertices).all() for m in s.geometry.values())
 deg=sum(int((m.area_faces<1e-12).sum()) for m in s.geometry.values());assert deg==0
 report[fname]={'meshes':len(s.geometry),'triangles':sum(len(m.faces) for m in s.geometry.values()),'degenerate':deg,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size_bytes':p.stat().st_size}
 if fname=='Locomotive_v3.glb':
  hull=s.geometry['body_UV_livery'];assert hull.visual.material.baseColorTexture.size==(4096,2048)
  report['texture']=list(hull.visual.material.baseColorTexture.size)
  # Exported glTF z=-authoring y. Test roof support using actual hull ray intersections; no optional rtree needed.
  bases=[(name,m) for name,m in s.geometry.items() if name.startswith('roof_hatch_base')];assert len(bases)==4
  checks=[]
  for name,m in bases:
   y0,y1=-m.bounds[1,2],-m.bounds[0,2];assert y1<2.30
   xs=np.linspace(m.bounds[0,0],m.bounds[1,0],5);zs=np.linspace(m.bounds[0,2],m.bounds[1,2],5)
   tri=hull.triangles; a=tri[:,0][:,[0,2]];b=tri[:,1][:,[0,2]];c=tri[:,2][:,[0,2]];v=b-a;w=c-a;det=v[:,0]*w[:,1]-v[:,1]*w[:,0];valid=abs(det)>1e-12
   heights=[]
   for x in xs:
    for z in zs:
     d=np.array([x,z])-a;u=np.divide(d[:,0]*w[:,1]-d[:,1]*w[:,0],det,out=np.zeros_like(det),where=valid);q=np.divide(v[:,0]*d[:,1]-v[:,1]*d[:,0],det,out=np.zeros_like(det),where=valid);ok=valid&(u>=-1e-7)&(q>=-1e-7)&(u+q<=1+1e-7)
     hh=tri[:,0,1]+u*(tri[:,1,1]-tri[:,0,1])+q*(tri[:,2,1]-tri[:,0,1]);assert ok.any();heights.append(hh[ok].max())
   gap=float(m.bounds[0,1]-min(heights));assert gap<.002, (name,gap)
   checks.append({'name':name,'longitudinal_range_BU':[float(y0),float(y1)],'max_base_bottom_minus_roof_BU':gap,'samples':25})
  report['roof_support']=checks
  shell=tm.util.concatenate([s.geometry[n] for n in ['body_UV_livery','rear_cap','nose_cap']]);shell.merge_vertices(merge_tex=True,merge_norm=True);report['hull_watertight']=bool(shell.is_watertight);report['hull_winding_consistent']=bool(shell.is_winding_consistent)
for n in ['hero','side','top','front','rear']:report[n+'_pixels']=list(Image.open(P/(n+'.png')).size)
(P/'qa.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
# before / after sheet with reference at top, actual model renders below
ref=Image.open(O/'Гибридный локомотив_ обновлённый облик.png').convert('RGB'); sheet=Image.new('RGB',(1800,1680),'#eef0f3');d=ImageDraw.Draw(sheet);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',25)
def place(im,box):
 im=im.copy();im.thumbnail((box[2],box[3]));sheet.paste(im,(box[0]+(box[2]-im.width)//2,box[1]+(box[3]-im.height)//2))
d.text((30,15),'REFERENCE / исходный эскиз',font=font,fill='#222');place(ref,(20,50,1760,740))
for i,(label,folder) in enumerate([('V2 / прежняя',O/'loco_v2'),('V3 / сглаженная',P)]):
 x=20+i*880;d.text((x,800),label,font=font,fill='#222');place(Image.open(folder/'hero.png'),(x,840,860,500));place(Image.open(folder/'top.png'),(x,1350,860,310))
sheet.save(O/'Locomotive_v3_comparison.png')
