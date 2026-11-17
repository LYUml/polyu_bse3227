import json,hashlib,itertools,math
from pathlib import Path
import numpy as np,ifcopenshell,ifcopenshell.geom,trimesh,ezdxf,manifold3d as mm
from bsa.solid_clash import from_mesh
from bsa.ifc_native import run
from outlet_native_batches import bounds,body,matrix
P=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');R=P/'07_Agent_Work/runs/logical-equipment-network/open-lined-plenum-reviewed';O=R/'details-plot-reviewed';O.mkdir(exist_ok=False);p=R/'Supply Air Open Plenum Candidate.ifc';m=ifcopenshell.open(str(p));r=json.loads((R/'review.json').read_text());records=r['records'];old=ifcopenshell.open(str(P/'07_Agent_Work/runs/logical-equipment-network/manufacturer-equipment-baseline/Supply Air Equipment Baseline.ifc'));changed={x['plenum_guid'] for x in records};others=[o for o in old.by_type('IfcDistributionElement') if o.GlobalId not in changed];assert len(others)==584;ob={o.GlobalId:bounds(body(o),matrix(o)) for o in others};new_collars=[]
for rec in records:
 F=np.array(rec['frame']);W,H,L,d,proj=[rec[k] for k in ['W','H','L','collar_OD','projection']]
 # Old occupied box encloses all new material except four outward collar stubs.
 verts=np.array(list(itertools.product([0,L],[-W/2,W/2],[-H/2,H/2])));w=verts@F[:3,:3].T+F[:3,3];a,b=bounds(body(old.by_guid(rec['plenum_guid'])),matrix(old.by_guid(rec['plenum_guid'])));assert np.allclose([w.min(axis=0),w.max(axis=0)],[a,b],atol=1e-8,rtol=0)
 for x in rec['stations']:
  for sign in [-1,1]:
   v=np.array(list(itertools.product([x-d/2,x+d/2],sorted([sign*W/2,sign*(W/2+proj)]),[-d/2,d/2])));v=v@F[:3,:3].T+F[:3,3];new_collars.append((rec['plenum_guid'],v.min(axis=0),v.max(axis=0)))
possible=[]
# Collar stubs outside all old plenum boxes and unchanged584body conservativebounds.
all_old={**ob,**{g:bounds(body(old.by_guid(g)),matrix(old.by_guid(g))) for g in changed}}
for i,(g,lo,hi) in enumerate(new_collars):
 for h,(a,b) in all_old.items():
  if h!=g and np.all(np.minimum(hi,b)-np.maximum(lo,a)>2e-5):possible.append([g,h])
 for h,a,b in new_collars[i+1:]:
  if np.all(np.minimum(hi,b)-np.maximum(lo,a)>2e-5):possible.append([g,h])
assert not possible,possible[:5]
coord=dict(unchanged584body_primitive_bounds_checked=True,all20old_box_bounds_match_new_chamber_envelopes=True,outside_collar_boxes_checked=80,new_positive_AABB_overlap_candidates=0,previous_collision_evidence_reused_only_for_unchanged_bodies_and_inside_old_solid_boxes=True,full_network_remesh=False,clearance_or_joint_acceptance=False)
(R/'geometry-coordination-handoff.json').write_text(json.dumps(coord,indent=2))
s=ifcopenshell.geom.settings();s.set(s.USE_WORLD_COORDS,True);s.set('mesher-linear-deflection',1e-5);doc=ezdxf.new('R2018');doc.units=6;doc.appids.new('BSA_IFC');ms=doc.modelspace()
for l in ['BSA_DETAIL_CUT','BSA_DETAIL_NOTES','BSA_SECTION_REFERENCE']:doc.layers.new(l)
views=[];counts={};control=None
for size,anchorx in [(12,.15),(14,1.65)]:
 rec=next(x for x in records if x['nominal_size_in']==size);obj=m.by_guid(rec['plenum_guid']);shape=ifcopenshell.geom.create_shape(s,obj);F=np.array(rec['frame']);v=(np.array(shape.geometry.verts).reshape(-1,3)-F[:3,3])@F[:3,:3];faces=np.array(shape.geometry.faces).reshape(-1,3);mesh=trimesh.Trimesh(vertices=v,faces=faces,process=False)
 if control is None:
  solid=from_mesh((v,faces));W,H,t,liner=[rec[k] for k in ['W','H','metal','liner']];block=mm.Manifold.cube((.01,W-2*(t+liner),H-2*(t+liner))).translate((.01,-W/2+t+liner,-H/2+t+liner));probe=mm.Manifold.cube((.04,(W-2*(t+liner))*.8,(H-2*(t+liner))*.8)).translate((0,-(W-2*(t+liner))*.4,-(H-2*(t+liner))*.4));good=(solid^probe).volume();bad=((solid+block)^probe).volume();assert abs(good)<1e-10 and bad>1e-5;control=dict(original_probe_overlap_m3=good,blocked_inlet_probe_overlap_m3=bad,blocked_airway_rejected=True)
 for title,normal,origin,u,v,anchor in [('PLAN',[0,0,1],[0,0,0],[1,0,0],[0,1,0],[anchorx,1.55]),('LONG SECTION',[0,1,0],[0,0,0],[1,0,0],[0,0,1],[anchorx,.9]),('OUTLET SECTION',[1,0,0],[rec['stations'][0],0,0],[0,1,0],[0,0,1],[anchorx,.23])]:
  seg=trimesh.intersections.mesh_plane(mesh,normal,origin);xy=np.stack([(seg-np.array(origin))@u,(seg-np.array(origin))@v],axis=-1);lo=xy.reshape(-1,2).min(axis=0);hi=xy.reshape(-1,2).max(axis=0);offset=np.array(anchor)-lo;count=0
  for a,b in xy:
   if np.linalg.norm(b-a)<1e-10:continue
   e=ms.add_line(tuple(a+offset),tuple(b+offset),dxfattribs={'layer':'BSA_DETAIL_CUT'});e.set_xdata('BSA_IFC',[(1000,obj.GlobalId)]);count+=1
  ms.add_text(f'Nominal {size}in / {title}',dxfattribs={'height':.028,'insert':(anchor[0],anchor[1]+hi[1]-lo[1]+.035),'layer':'BSA_DETAIL_NOTES'});views.append(dict(size=size,view=title,source_guid=obj.GlobalId,cut_segments=count));counts[obj.GlobalId]=counts.get(obj.GlobalId,0)+count
for t,y,h in [('OPEN LINED PLENUM CONSTRUCTION CANDIDATE',2.48,.042),('Actual saved material sections | combined liner + metal volume | 1:12.5',2.40,.028),('Assumed metal0.8mm;source standard liner12.7mm;no balancing damper blades',.105,.019),('W/H outside interpretation,collar lining,slip-drive overlap and joint fit remain unverified',.065,.017),('Geometry only:pressure,installed product and full design are not accepted',.025,.019)]:ms.add_text(t,dxfattribs={'height':h,'insert':(.15,y),'layer':'BSA_DETAIL_NOTES'})
e=ms.add_line((.9,.18),(1.15,.18),dxfattribs={'layer':'BSA_SECTION_REFERENCE'});e.set_xdata('BSA_IFC',[(1000,records[0]['plenum_guid'])]);ms.add_text('0.25m',dxfattribs={'height':.019,'insert':(1.18,.17),'layer':'BSA_DETAIL_NOTES'})
dxf=O/'Open Lined Plenum Details.dxf';doc.saveas(dxf);sheet=dict(source='Actual saved20linedplenumcandidate;two nominal sizes withplan,long andoutlet materialcuts',window_drawing_units=[0,0,3.65,2.55],scale_denominator=12.5,reference_ifc_guid=records[0]['plenum_guid'],reference_layer='BSA_SECTION_REFERENCE',drawing_name='section',pdf_tolerance_mm=.3);(O/'sheet.json').write_text(json.dumps(sheet,indent=2));(R/'blocked-airway-control.json').write_text(json.dumps(control,indent=2));n=run(dxf,O/'sheet.json',O/'native','C:/Program Files/Autodesk/AutoCAD 2027/accoreconsole.exe');(O/'projection.json').write_text(json.dumps(dict(ifc_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),represented_plenums=2,views=views,source_cut_counts=counts,native_reopen_pass=n['native_reopen_pass'],visual_review='pending',design_accepted=False),indent=2));print('Two size families/six actual material sections saved and reopened')
