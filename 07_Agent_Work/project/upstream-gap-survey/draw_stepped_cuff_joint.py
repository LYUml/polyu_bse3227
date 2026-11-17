import json,hashlib
from pathlib import Path
import numpy as np,manifold3d as mm,ifcopenshell,ifcopenshell.geom,ezdxf,trimesh
from ifcopenshell.util import placement
from shapely.geometry import LineString,box
from bsa.solid_clash import from_mesh
from bsa.ifc_native import run
P=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');R=P/'07_Agent_Work/runs/logical-equipment-network/stepped-cuff-joint-reviewed';O=R/'detail-reviewed';O.mkdir(exist_ok=False);p=R/'Supply Air Stepped Joint Candidate.ifc';s=json.loads((R/'review.json').read_text());rec=s['records'][0];m=ifcopenshell.open(str(p));air=[]
for kind in ['sleeve','bondlines']:
 d=np.load(R/(kind+'-native.npz'));solid=from_mesh((d['vertices'],d['faces']));vols=[]
 for y0,y1,diam in [(-rec['half_length_m']-.001,0,rec['upstream_ID_m']),(0,rec['half_length_m']+.001,rec['downstream_ID_m'])]:
  probe=mm.Manifold.cylinder(y1-y0,diam/2-.00005,diam/2-.00005,128);F=np.array([[1,0,0,0],[0,0,1,y0],[0,-1,0,0]],float);common=solid^probe.transform(F);assert common.status()==mm.Error.NoError and abs(common.volume())<1e-10;vols.append(common.volume())
 air.append(dict(kind=kind,native_air_probe_overlap_m3=vols))
(R/'airway-probe-review.json').write_text(json.dumps(dict(canonical_native_air_probes=air,whole_product_shape_instances=160,actual_bore_intrusion=False,pressure_or_leakage_test=False),indent=2))
F=np.array(rec['frame']);settings=ifcopenshell.geom.settings();settings.set(settings.USE_WORLD_COORDS,True);settings.set('mesher-linear-deflection',1e-5);source=m.by_guid(rec['plenum_guid']);shape=ifcopenshell.geom.create_shape(settings,source);v=(np.array(shape.geometry.verts).reshape(-1,3)-F[:3,3])@F[:3,:3];faces=np.array(shape.geometry.faces).reshape(-1,3);mesh=trimesh.Trimesh(vertices=v,faces=faces,process=False);seg=trimesh.intersections.mesh_plane(mesh,[0,0,1],[0,0,0]);cuts=[(rec['plenum_guid'],'BSA_EXISTING_MATERIAL',q[:,[1,0]]) for q in seg]
for key,layer in [('reducer_guid','BSA_EXISTING_MATERIAL'),('sleeve_guid','BSA_SLEEVE'),('bondline_guid','BSA_BONDLINE')]:
 obj=m.by_guid(rec[key])
 for solid in obj.Representation.Representations[0].Items:
  pts=np.array([x.Coordinates for x in solid.SweptArea.OuterCurve.Points]);assert len(pts)>3
  for sign in [-1,1]:
   xy=np.column_stack([pts[:,1],sign*pts[:,0]])
   for a,b in zip(xy,xy[1:]):cuts.append((obj.GlobalId,layer,np.array([a,b])))
doc=ezdxf.new('R2018');doc.units=6;doc.appids.new('BSA_IFC');ms=doc.modelspace()
for layer,color in [('BSA_EXISTING_MATERIAL',7),('BSA_SLEEVE',1),('BSA_BONDLINE',5),('BSA_JOINT_NOTES',7),('BSA_SECTION_REFERENCE',7),('BSA_AXIS',8)]:doc.layers.new(layer,dxfattribs={'color':color})
clip=box(-.05,-.14,.10,.14);offset=np.array([.11,.19]);counts={}
for g,layer,seg in cuts:
 q=LineString(seg).intersection(clip)
 if q.is_empty:continue
 pieces=list(q.geoms) if hasattr(q,'geoms') else [q]
 for part in pieces:
  if part.geom_type!='LineString' or part.length<1e-10:continue
  coords=np.array(part.coords)+offset
  for a,b in zip(coords,coords[1:]):
   e=ms.add_line(tuple(a),tuple(b),dxfattribs={'layer':layer});e.set_xdata('BSA_IFC',[(1000,g)]);counts[g]=counts.get(g,0)+1
assert len(counts)==4 and all(counts.values())
ms.add_line((.06,.19),(.21,.19),dxfattribs={'layer':'BSA_AXIS'})
for t,y,h in [('STEPPED OUTER SLEEVE JOINT CANDIDATE',.383,.007),('Actual saved material section / cropped context / 1:2',.364,.0048)]:ms.add_text(t,dxfattribs={'height':h,'insert':(.02,y),'layer':'BSA_JOINT_NOTES'})
notes=['PROPOSED CUSTOM JOINT / NOT APPROVED','Existing collar OD:250.825mm','Existing reducer ID/OD:254/255.6mm','Candidate sleeve OD:258.8mm','Overlap each side:25.4mm assumed','Bondline proxy:0.8mm assumed','Minimum sleeve wall:0.8mm assumed','Upstream sleeve wall:3.1875mm','Contours:sleeve and bondline proxies','Centre line:reference flow axis','Original bodies and ports retained','Mechanical fasteners not modelled','Cure,shrinkage and adhesion unverified','No airtightness or pressure acceptance','Metal method is not UL181 closure']
for i,t in enumerate(notes):ms.add_text(t,dxfattribs={'height':.0044,'insert':(.26,.334-i*.019),'layer':'BSA_JOINT_NOTES'})
e=ms.add_line((.07,.025),(.09,.025),dxfattribs={'layer':'BSA_SECTION_REFERENCE'});e.set_xdata('BSA_IFC',[(1000,rec['sleeve_guid'])]);ms.add_text('20mm reference',dxfattribs={'height':.004,'insert':(.10,.023),'layer':'BSA_JOINT_NOTES'});ms.add_text('Bondline dimensions are design proxies,not manufacturer specified cured thickness.',dxfattribs={'height':.0038,'insert':(.02,.008),'layer':'BSA_JOINT_NOTES'})
dxf=O/'Stepped Sleeve Joint Detail.dxf';doc.saveas(dxf);sheet=dict(source='Actual savedplenum collar,reducer,customsleeveandbondlineproxysections;nominaljointcandidate',window_drawing_units=[0,0,.58,.405],scale_denominator=2,reference_ifc_guid=rec['sleeve_guid'],reference_layer='BSA_SECTION_REFERENCE',drawing_name='section',pdf_tolerance_mm=.3);(O/'sheet.json').write_text(json.dumps(sheet,indent=2));n=run(dxf,O/'sheet.json',O/'native','C:/Program Files/Autodesk/AutoCAD 2027/accoreconsole.exe');(O/'projection.json').write_text(json.dumps(dict(ifc_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),represented_products=4,source_guid_cut_counts=counts,native_reopen_pass=n['native_reopen_pass'],visual_review='pending',design_accepted=False),indent=2));print('Four actual product sections in native DWG reopened and plotted')
