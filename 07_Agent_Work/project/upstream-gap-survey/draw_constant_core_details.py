import json,hashlib
from pathlib import Path
import numpy as np,ifcopenshell,ifcopenshell.geom,trimesh,ezdxf
from bsa.ifc_native import run
R=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/equal-cross-compound-core-candidate');O=R/'details';O.mkdir(exist_ok=False);p=R/'Supply Network.ifc';m=ifcopenshell.open(str(p));review=json.loads((R/'transition-source-review.json').read_text());core=m.by_guid('3tK$ugPAvIAAusb9mKjQEp');objects=[core]+[m.by_guid(r['product_guid']) for r in review['records']];origin=np.array([86.5,35.58058400000001,0.]);s=ifcopenshell.geom.settings();s.set(s.USE_WORLD_COORDS,True);meshes={}
for o in objects:
 shape=ifcopenshell.geom.create_shape(s,o);meshes[o.GlobalId]=trimesh.Trimesh(vertices=np.array(shape.geometry.verts).reshape(-1,3),faces=np.array(shape.geometry.faces).reshape(-1,3),process=False)
doc=ezdxf.new('R2018');doc.units=6;doc.appids.new('BSA_IFC');ms=doc.modelspace()
for l in ['BSA_DETAIL_CUT','BSA_DETAIL_NOTES','BSA_SECTION_REFERENCE']:doc.layers.new(l)
counts={};views=[]
for title,normal,u,v,anchor in [('PLAN / z=0',[0,0,1],[1,0,0],[0,1,0],[.3,2.5]),('TRUNK SIDE / x=0',[1,0,0],[0,0,1],[0,1,0],[5.5,2.5]),('LOWER BRANCH SIDE / y=0',[0,1,0],[1,0,0],[0,0,1],[4.3,.8])]:
 cuts=[]
 for g,mesh in meshes.items():
  seg=trimesh.intersections.mesh_plane(mesh,normal,origin)
  if len(seg):cuts.append((g,np.stack([(seg-origin)@np.array(u),(seg-origin)@np.array(v)],axis=-1)))
 pts=np.concatenate([xy.reshape(-1,2) for _,xy in cuts]);lo=pts.min(axis=0);hi=pts.max(axis=0);offset=np.array(anchor)-lo
 for g,segments in cuts:
  for seg in segments:
   if np.linalg.norm(seg[1]-seg[0])<1e-10:continue
   e=ms.add_line(tuple(seg[0]+offset),tuple(seg[1]+offset),dxfattribs={'layer':'BSA_DETAIL_CUT'});e.set_xdata('BSA_IFC',[(1000,g)]);counts[g]=counts.get(g,0)+1
 ms.add_text(title,dxfattribs={'height':.045,'insert':(anchor[0],anchor[1]+hi[1]-lo[1]+.13),'layer':'BSA_DETAIL_NOTES'});views.append(title)
assert len(counts)==7 and all(counts.values())
notes=[('CONSTANT JUNCTION CORE DETAILS',5.68,.08),('Actual saved plan and side material sections | 1:20',5.42,.048),('Core1350x900;upper branch500x900;opposed lower branches600x900mm',5.19,.044),('Six external45degree contractions restore inherited downstream sizes',4.98,.044),('Clear axial gap between branch apertures:69.416mm',.50,.04),('Assumed gauge0.8mm,collars50mm;existing upper-cap clearance37.5mm',.32,.04),('Close coupling,pressure stations,friction,noise and complete pressure remain unresolved',.14,.04)]
for text,y,h in notes:ms.add_text(text,dxfattribs={'height':h,'insert':(.3,y),'layer':'BSA_DETAIL_NOTES'})
e=ms.add_line((.3,1.3),(.8,1.3),dxfattribs={'layer':'BSA_SECTION_REFERENCE'});e.set_xdata('BSA_IFC',[(1000,core.GlobalId)]);ms.add_text('0.5m reference',dxfattribs={'height':.04,'insert':(.95,1.28),'layer':'BSA_DETAIL_NOTES'})
dxf=O/'Constant Junction Core Details.dxf';doc.saveas(dxf);sheet=dict(source='Actual164body network core plus six native contractions,3cuts',window_drawing_units=[0,0,8.4,5.94],scale_denominator=20,reference_ifc_guid=core.GlobalId,reference_layer='BSA_SECTION_REFERENCE',drawing_name='section',pdf_tolerance_mm=.3);(O/'sheet.json').write_text(json.dumps(sheet,indent=2));n=run(dxf,O/'sheet.json',O/'native');(O/'projection.json').write_text(json.dumps(dict(ifc_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),represented_products=7,views=views,native_product_section_counts=counts,native_reopen_pass=n['native_reopen_pass'],visual_review='pending',design_accepted=False),indent=2));print('7actual bodies in3native detail views saved/reopened')
