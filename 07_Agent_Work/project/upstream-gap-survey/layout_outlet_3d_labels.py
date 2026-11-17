import json,math
from pathlib import Path
import numpy as np,ezdxf
from shapely.geometry import LineString,Point,box
from shapely.strtree import STRtree
from ezdxf.path import make_path
from bsa.cad_text_layout import text_box
R=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/three-dimensional-outlet-candidate');S=R/'drawing-reviewed';O=R/'drawing-readable-screened';O.mkdir(exist_ok=False);d=ezdxf.readfile(S/'Supply and Three Dimensional Branch Connections.dxf');ms=d.modelspace();projection=json.loads((S/'projection.json').read_text());markers={r['terminal']:np.array(ms.doc.entitydb[r['terminal_marker_handle']].dxf.center)[:2] for r in projection['records']}
for e in ms:
 if e.dxftype()=='LINE' and e.dxf.layer=='BSA_SECTION_REFERENCE':e.dxf.start=(2.,31.5,0.);e.dxf.end=(12.,31.5,0.)
 if e.dxftype()=='TEXT' and e.dxf.text=='10m reference':e.dxf.insert=(12.7,31.3,0.)
graphics=[];reserved=[]
for e in ms:
 if e.dxftype()=='LINE':graphics.append(LineString([tuple(e.dxf.start)[:2],tuple(e.dxf.end)[:2]]))
 elif e.dxftype()=='LWPOLYLINE':graphics.append(LineString([tuple(p)[:2] for p in make_path(e).flattening(.02)]))
 elif e.dxftype()=='CIRCLE':graphics.append(Point(tuple(e.dxf.center)[:2]).buffer(e.dxf.radius))
 elif e.dxftype()=='TEXT' and e.dxf.layer!='BSA_BRANCH_LABEL':reserved.append(box(*text_box(e)).buffer(.06))
tree=STRtree(graphics);placed=[];records=[]
for e in sorted([e for e in ms if e.dxftype()=='TEXT' and e.dxf.layer=='BSA_BRANCH_LABEL'],key=lambda e:e.dxf.text):
 e.dxf.height=.36;anchor=markers[e.dxf.text];bb=text_box(e);centre=(bb[:2]+bb[2:])/2;shape=bb[2:]-bb[:2];selected=None
 for distance in [.5,.65,.8,1.,1.2,1.4,1.6,1.8,2.]:
  for angle in [k*math.pi/8 for k in [4,12,0,8,2,6,14,10,1,3,5,7,9,11,13,15]]:
   target=anchor+distance*np.array([math.cos(angle),math.sin(angle)]);lo=target-shape/2;hi=target+shape/2;poly=box(*lo,*hi).buffer(.06)
   if lo[0]<.1 or hi[0]>57.9 or lo[1]<3.5 or hi[1]>33.5:continue
   if len(tree.query(poly,predicate='intersects')) or any(poly.intersects(p) for p in reserved+placed):continue
   if any(np.linalg.norm(target-other)<=distance+.1 for name,other in markers.items() if name!=e.dxf.text):continue
   selected=target;placed.append(poly);break
  if selected is not None:break
 assert selected is not None,e.dxf.text;delta=selected-centre;e.dxf.insert=(e.dxf.insert.x+delta[0],e.dxf.insert.y+delta[1],0.);records.append(dict(terminal=e.dxf.text,anchor_m=anchor.tolist(),label_centre_m=selected.tolist(),distance_m=float(np.linalg.norm(selected-anchor))))
assert len(records)==80;p=O/'Supply and Three Dimensional Branch Connections.dxf';d.saveas(p);projection.update(native_reopen_pass=False,visual_review='pending',terminal_label_boxes_avoid_graphics_and_each_other=True,label_associations=records);(O/'projection.json').write_text(json.dumps(projection,indent=2));(O/'sheet.json').write_text((S/'sheet.json').read_text());print('80labels placedwithnativefontbounds+STRtree;reference moved clear')
S=R/'detail-reviewed';O=R/'detail-readable-screened';O.mkdir(exist_ok=False);d=ezdxf.readfile(S/'Terminal Turn Connection Detail.dxf')
for e in d.modelspace().query('TEXT'):
 if e.dxf.text=='TERMINAL TURN CONNECTION DETAIL':e.dxf.height=.06;e.dxf.insert=(.15,2.75,0.)
d.saveas(O/'Terminal Turn Connection Detail.dxf');(O/'sheet.json').write_text((S/'sheet.json').read_text());p=json.loads((S/'projection.json').read_text());p.update(native_reopen_pass=False,visual_review='pending');(O/'projection.json').write_text(json.dumps(p,indent=2))

