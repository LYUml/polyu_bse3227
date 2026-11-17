import json,math,hashlib
from pathlib import Path
import numpy as np,ifcopenshell,ifcopenshell.geom,ifcopenshell.validate
from ifcopenshell.util import placement,system
from bsa.circular_native import straight_wall
from bsa.round_bend_quantities import calculate
from bsa.circular_geometry import configure
from bsa.solid_clash import from_mesh,overlaps
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs');R=B/'three-dimensional-outlet-candidate';p=R/'Supply and Three Dimensional Outlet Candidate.ifc';review=json.loads((R/'review.json').read_text());m=ifcopenshell.open(str(p));s=ifcopenshell.geom.settings();s.set(s.USE_WORLD_COORDS,True);configure(s);meshes={};checks=[];D=review['assumptions']['bore_m'];g=review['assumptions']['gauge_m'];area=math.pi*((D/2+g)**2-(D/2)**2);maximum=0
for r in review['records']:
 for piece in r['pieces']:
  obj=m.by_guid(piece['guid']);native=straight_wall(obj) if piece['kind']=='straight' else calculate(obj);L=native['length_m'] if piece['kind']=='straight' else native['centreline_length_m'];assert math.isclose(L,piece['length_m'],rel_tol=1e-8);assert math.isclose(native['inner_m'],D,rel_tol=1e-12);shape=ifcopenshell.geom.create_shape(s,obj);v=np.asarray(shape.geometry.verts).reshape(-1,3);f=np.asarray(shape.geometry.faces).reshape(-1,3);meshes[obj.GlobalId]=(v.tolist(),f.tolist());solid=from_mesh((v,f));assert solid.volume()>0 and len(solid.decompose())==1;err=abs(solid.volume()/(area*L)-1);maximum=max(maximum,err);assert err<.001
  for port in system.get_ports(obj):
   frame=placement.get_local_placement(port.ObjectPlacement);local=(v-frame[:3,3])@frame[:3,:3];selected=f[np.max(abs(local[f,2]),axis=1)<1e-8];assert len(selected)>0;points=local[np.unique(selected),:2];rad=np.linalg.norm(points,axis=1);assert abs(min(rad)-D/2)<1e-8 and abs(max(rad)-(D/2+g))<1e-8;assert max(np.minimum(abs(rad-D/2),abs(rad-(D/2+g))))<1e-8
  checks.append(dict(guid=obj.GlobalId,kind=piece['kind'],native_length_m=L,volume_relative_error=err))
assert len(checks)==320
# Check all320 added physical interfaces,including reducer-to-lead.
added={r['guid'] for r in checks};links=[]
for link in m.by_type('IfcRelConnectsPorts'):
 a,b=link.RelatingPort,link.RelatedPort;oa,ob=system.get_port_element(a),system.get_port_element(b)
 if oa.GlobalId not in added and ob.GlobalId not in added:continue
 f1,f2=[placement.get_local_placement(p.ObjectPlacement) for p in [a,b]];assert a.FlowDirection=='SOURCE' and b.FlowDirection=='SINK';assert np.allclose(f1[:3,3],f2[:3,3],atol=1e-9,rtol=0) and np.allclose(f1[:3,2],-f2[:3,2],atol=1e-9,rtol=0);links.append([a.GlobalId,b.GlobalId])
assert len(links)==320
logger=ifcopenshell.validate.json_logger();ifcopenshell.validate.validate(m,logger,express_rules=True);assert not logger.statements
result=dict(ifc_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),native_branch_body_count=320,native_bends=160,native_straights=160,positive_closed_connected_solids=320,annular_face_ports_checked=640,new_interfaces_checked=320,schema_express_errors=0,maximum_native_volume_relative_error=maximum,records=checks,reader_sha256=hashlib.sha256(Path('src/bsa/round_bend_quantities.py').read_bytes()).hexdigest(),full_pressure_verified=False,design_accepted=False);(R/'native-review.json').write_text(json.dumps(result,indent=2));print('320nativebodies/640annularports/320newinterfaces/schemaPASS',flush=True)
els=[e for e in m.by_type('IfcElement') if e.Representation and not any(x in (e.Name or '') for x in ['RESERVATION'])];assert len(els)==604
for e in els:
 if e.GlobalId in meshes:continue
 shape=ifcopenshell.geom.create_shape(s,e);meshes[e.GlobalId]=(list(shape.geometry.verts),list(shape.geometry.faces))
f,u,n,c=overlaps(els,meshes,2e-5,1e-10,5000);report=dict(ifc_sha256=result['ifc_sha256'],physical_scope_bodies=604,excluded_nonphysical_reservations=60,intersection_count=len(f),unverified=u,boolean_candidates=n,findings=f,design_accepted=False);(R/'intersection-review.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
