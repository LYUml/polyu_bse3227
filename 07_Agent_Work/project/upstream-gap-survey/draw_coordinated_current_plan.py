import json,math,hashlib
from pathlib import Path
import numpy as np,ezdxf,ifcopenshell,ifcopenshell.geom,trimesh
from ifcopenshell.util.placement import get_local_placement,get_axis2placement
from shapely.geometry import LineString,box
from shapely.strtree import STRtree
from ezdxf.path import make_path
from bsa.cad_text_layout import text_box
P=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227');R=P/'07_Agent_Work/runs/logical-equipment-network';C=R/'stepped-cuff-joint-reviewed';O=R/'coordinated-current-plan';O.mkdir(exist_ok=False);source=C/'Supply Air Stepped Joint Candidate.ifc';m=ifcopenshell.open(str(source));old=R/'drawing/Supply Air Logical Network.dxf';doc=ezdxf.readfile(old);ms=doc.modelspace();integration=json.loads((R/'integration.json').read_text());joints=json.loads((C/'review.json').read_text())['records'];offset=np.array(json.loads((R/'drawing/projection.json').read_text())['common_xy_translation_m']);plenum_guids={x['plenum_guid'] for x in integration['records']};removed=0
for e in list(ms):
 if e.dxf.layer=='BSA_EQUIPMENT_ENVELOPE' and e.has_xdata('BSA_IFC') and any(t.value in plenum_guids for t in e.get_xdata('BSA_IFC')):ms.delete_entity(e);removed+=1
assert removed==20
for layer in ['BSA_PLENUM_MATERIAL','BSA_JOINT_MATERIAL','BSA_BONDLINE_PROXY']:doc.layers.new(layer,dxfattribs={'color':7})
settings=ifcopenshell.geom.settings();settings.set(settings.USE_WORLD_COORDS,True);settings.set('mesher-linear-deflection',1e-5);counts={}
for g in sorted(plenum_guids):
 obj=m.by_guid(g);shape=ifcopenshell.geom.create_shape(settings,obj);mesh=trimesh.Trimesh(vertices=np.array(shape.geometry.verts).reshape(-1,3),faces=np.array(shape.geometry.faces).reshape(-1,3),process=False);segments=trimesh.intersections.mesh_plane(mesh,[0,0,1],[0,0,0]);count=0
 for seg in segments:
  a,b=seg[:,:2]+offset
  if np.linalg.norm(a-b)<1e-10:continue
  e=ms.add_line(tuple(a),tuple(b),dxfattribs={'layer':'BSA_PLENUM_MATERIAL'});e.set_xdata('BSA_IFC',[(1000,g)]);count+=1
 assert count>0;counts[g]=count
for rec in joints:
 for key,layer in [('sleeve_guid','BSA_JOINT_MATERIAL'),('bondline_guid','BSA_BONDLINE_PROXY')]:
  obj=m.by_guid(rec[key]);F=get_local_placement(obj.ObjectPlacement);assert abs(F[2,3])<1e-10 and abs(F[2,1])<1e-10 and np.allclose(F[:3,:3].T@F[:3,:3],np.eye(3),atol=1e-10,rtol=0);u=F[:3,1];normal=np.cross([0,0,1],u);assert math.isclose(np.linalg.norm(normal),1,abs_tol=1e-10);count=0
  for solid in obj.Representation.Representations[0].Items:
   assert solid.is_a('IfcRevolvedAreaSolid') and math.isclose(solid.Angle,2*math.pi,abs_tol=1e-10) and np.allclose(get_axis2placement(solid.Position),np.eye(4),atol=1e-10,rtol=0) and tuple(solid.Axis.Location.Coordinates)==(0.,0.,0.) and tuple(solid.Axis.Axis.DirectionRatios)==(0.,1.,0.)
   pts=np.array([p.Coordinates for p in solid.SweptArea.OuterCurve.Points]);assert np.array_equal(pts[0],pts[-1])
   for sign in [-1,1]:
    xy=np.array([(F[:3,3]+u*t+normal*sign*r)[:2]+offset for r,t in pts[:-1]]);e=ms.add_lwpolyline([tuple(q) for q in xy],close=True,dxfattribs={'layer':layer});e.set_xdata('BSA_IFC',[(1000,obj.GlobalId)]);count+=1
  counts[obj.GlobalId]=count
for e in ms.query('TEXT'):
 t=e.dxf.text
 if t.startswith('LOGICAL SUPPLY'):e.dxf.text='COORDINATED SUPPLY AIR CANDIDATE'
 elif t.startswith('Main/reducer material'):e.dxf.text='Main/reducer/plenum material sections + branch axes + nominal joints | 1:200'
 elif t.startswith('One logical tree'):e.dxf.text='604 flow products + 160 joint accessories;60 nonphysical reservations omitted'
 elif t.startswith('Equipment outlines:'):e.dxf.text='VAV envelopes;logical dashed axes;custom joints unapproved;see separate details'
 elif t.startswith('194conditional'):e.dxf.text='374 conditional values / 84 numeric gaps;full pressure and design acceptance pending'
# Check actual GUID coverage and unchanged existing 100 label placements.
expected={o.GlobalId for o in m.by_type('IfcDistributionElement')}|{o.GlobalId for o in m.by_type('IfcDiscreteAccessory')};actual={t.value for e in ms if e.has_xdata('BSA_IFC') for t in e.get_xdata('BSA_IFC') if t.code==1000};assert expected==actual and len(actual)==764
newgraphics=[]
for e in ms:
 if e.dxf.layer not in ['BSA_PLENUM_MATERIAL','BSA_JOINT_MATERIAL','BSA_BONDLINE_PROXY']:continue
 if e.dxftype()=='LINE':newgraphics.append(LineString([tuple(e.dxf.start)[:2],tuple(e.dxf.end)[:2]]))
 elif e.dxftype()=='LWPOLYLINE':newgraphics.append(LineString([tuple(p)[:2] for p in make_path(e).flattening(.001)]))
tree=STRtree(newgraphics);collisions=[]
for e in ms.query('TEXT'):
 if e.dxf.layer in ['BSA_VAV_LABEL','BSA_BRANCH_LABEL'] and len(tree.query(box(*text_box(e)).buffer(.06),predicate='intersects')):collisions.append(e.dxf.text)
assert not collisions,collisions
out=O/'Coordinated Supply Air Candidate.dxf';doc.saveas(out);spec=json.loads((R/'drawing/settings.json').read_text());spec['source_sha256']=hashlib.sha256(out.read_bytes()).hexdigest();spec['layers']=sorted({e.dxf.layer for e in ms});spec['sheet']['source']='Current saved candidate;actual plenum/joint sections and unchanged branch axes;not approved for construction';(O/'settings.json').write_text(json.dumps(spec,indent=2));review={'source_ifc_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_dxf_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'drawing_sha256':spec['source_sha256'],'represented_flow_products':604,'represented_accessories':160,'source_guids':sorted(actual),'changed_material_source_counts':counts,'removed_old_plenum_envelopes':20,'new_material_label_collision_count':len(collisions),'native_reopen_pass':False,'visual_review':'pending','design_accepted':False,'scope':'Candidate plan;VAV outside envelopes and branch axes remain schematic;source assumptions and unapproved joints retained'};(O/'projection.json').write_text(json.dumps(review,indent=2));print('Prepared current candidate plan:764GUIDs,20actualplenumsections,160jointaccessories,labelcollision0')
