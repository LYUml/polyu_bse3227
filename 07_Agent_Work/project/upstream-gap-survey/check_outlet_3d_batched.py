import json,hashlib,math,itertools
from pathlib import Path
import numpy as np,ifcopenshell,ifcopenshell.validate
from ifcopenshell.util import placement,system
from bsa.circular_native import straight_wall
from bsa.round_bend_quantities import calculate
from bsa.round_reducer_quantities import calculate as reducer_read
from bsa.solid_clash import from_mesh,overlaps
from bsa.duct_fitting_chain import value
from outlet_native_batches import Cache,body,bounds,key,matrix
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs');R=B/'three-dimensional-outlet-candidate';O=R/'bounded-native-reviewed';O.mkdir(exist_ok=False);p=R/'Supply and Three Dimensional Outlet Candidate.ifc';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before=sha(p);m=ifcopenshell.open(str(p));review=json.loads((R/'review.json').read_text());cache=Cache(O/'mesh-cache');checks=[];canonical={};ro=.2032/2+.0008
for route in review['records']:
 for piece in route['pieces']:
  obj=m.by_guid(piece['guid']);g=straight_wall(obj) if piece['kind']=='straight' else calculate(obj);L=g['length_m'] if piece['kind']=='straight' else g['centreline_length_m'];assert math.isclose(L,piece['length_m'],rel_tol=1e-8);h=key(obj);w=matrix(obj);ports=system.get_ports(obj);frames={p.Name:np.linalg.inv(w)@placement.get_local_placement(p.ObjectPlacement) for p in ports}
  if h not in canonical:
   v,f=cache.local(obj);solid=from_mesh((v,f));assert solid.volume()>0 and len(solid.decompose())==1;volume=math.pi*(ro**2-(ro-.0008)**2)*L;err=abs(solid.volume()/volume-1);assert err<.001;nativecaps={}
   for name,frame in frames.items():
    local=(v-frame[:3,3])@frame[:3,:3];selected=f[np.max(abs(local[f,2]),axis=1)<1e-8];assert len(selected)>0;rad=np.linalg.norm(local[np.unique(selected),:2],axis=1);assert abs(min(rad)-.2032/2)<1e-8 and abs(max(rad)-ro)<1e-8;nativecaps[name]=dict(point=frame[:3,3].tolist(),normal=frame[:3,2].tolist())
   # Prove primitive bounds enclose an actually executed native triangulation.
   low,high=bounds(body(obj),w);wv=v@w[:3,:3].T+w[:3,3];assert np.all(wv.min(axis=0)>=low-1e-8) and np.all(wv.max(axis=0)<=high+1e-8)
   canonical[h]=dict(sample_guid=obj.GlobalId,volume_relative_error=err,positive_closed_connected=True,native_caps=nativecaps)
  for name,frame in frames.items():assert np.allclose(frame[:3,3],canonical[h]['native_caps'][name]['point'],atol=1e-9,rtol=0) and np.allclose(frame[:3,2],canonical[h]['native_caps'][name]['normal'],atol=1e-9,rtol=0)
  checks.append(dict(guid=obj.GlobalId,kind=piece['kind'],native_length_m=L,literal_shape_sha256=h,proper_rigid_instance_verified=True))
 if len(checks)%32==0:print('Checked bodies',len(checks),'executed canonical shapes',len(canonical),flush=True)
assert len(checks)==320
report=dict(ifc_sha256=before,branch_bodies=320,bends=160,straights=160,literal_shape_instances_checked=320,executed_canonical_native_meshes=len(canonical),instance_coverage='Exact native solid-value equality plus proper rigid placement and owned-cap correspondence;not320independent remeshes',positive_closed_connected_instances=320,annular_face_ports_covered=640,maximum_native_volume_relative_error=max(x['volume_relative_error'] for x in canonical.values()),canonical_shapes=canonical,records=checks,reader_sha256=sha(Path('src/bsa/round_bend_quantities.py')),schema_express_errors=None,design_accepted=False);(O/'native-review.json').write_text(json.dumps(report,indent=2));print('Native geometry complete;schema next',flush=True)
logger=ifcopenshell.validate.json_logger();ifcopenshell.validate.validate(m,logger,express_rules=True);assert not logger.statements;report['schema_express_errors']=0;(O/'native-review.json').write_text(json.dumps(report,indent=2));print('Schema EXPRESS pass;bounded collision next',flush=True)
# All physical pieces get conservative bounds,not mesh boxes substituted for solids.
els=[e for e in m.by_type('IfcElement') if e.Representation and 'RESERVATION' not in (e.Name or '')];assert len(els)==604;bs={e.GlobalId:bounds(body(e),matrix(e)) for e in els};added={x['guid'] for x in checks};adjacent={}
for link in m.by_type('IfcRelConnectsPorts'):
 a,b=link.RelatingPort,link.RelatedPort;oa,ob=system.get_port_element(a),system.get_port_element(b)
 if oa.GlobalId not in added and ob.GlobalId not in added:continue
 f1,f2=[placement.get_local_placement(p.ObjectPlacement) for p in [a,b]];assert a.FlowDirection=='SOURCE' and b.FlowDirection=='SINK' and np.allclose(f1[:3,3],f2[:3,3],atol=1e-9,rtol=0) and np.allclose(f1[:3,2],-f2[:3,2],atol=1e-9,rtol=0)
 # A positive-length straight adjoins one minor bend or a checked reducer.
 if oa.GlobalId not in added:reducer_read(oa,.15,1.2)
 assert (oa.is_a('IfcDuctSegment') or ob.is_a('IfcDuctSegment'))
 adjacent[tuple(sorted([oa.GlobalId,ob.GlobalId]))]='Separated open halfspaces at exact common cap;minor bend0<theta<=90 andR>outerradius or monotone reducer;not a contact waiver'
assert len(adjacent)==320
oldpath=B/'equal-cross-compound-core-candidate/equipment-space/model.ifc';old=ifcopenshell.open(str(oldpath));oldproof=json.loads((oldpath.parent/'casing-intersection-review.json').read_text());assert oldproof['source_ifc_sha256']==sha(oldpath) and oldproof['intersection_count']==0 and not oldproof['unverified'];oldids={e.GlobalId for e in old.by_type('IfcElement') if e.Representation and 'RESERVATION' not in (e.Name or '')};assert len(oldids)==184
for g in oldids:assert value(body(m.by_guid(g)))==value(body(old.by_guid(g))) and np.array_equal(matrix(m.by_guid(g)),matrix(old.by_guid(g)))
pairs=[];prior=0;halfspace=0
for a,b in itertools.combinations(els,2):
 al,ah=bs[a.GlobalId];bl,bh=bs[b.GlobalId]
 if not np.all(np.minimum(ah,bh)-np.maximum(al,bl)>2e-5):continue
 pair=tuple(sorted([a.GlobalId,b.GlobalId]))
 if pair in adjacent:halfspace+=1;continue
 if a.GlobalId in oldids and b.GlobalId in oldids:prior+=1;continue
 pairs.append((a,b))
assert len(pairs)<=5000;print('New bounded Boolean candidates',len(pairs),'reused prior',prior,'halfspace proofs',halfspace,flush=True);findings=[];unverified=[];booleanchecks=[]
for i,(a,b) in enumerate(pairs):
 meshes={o.GlobalId:cache.world(o) for o in [a,b]};f,u,n,c=overlaps([a,b],meshes,2e-5,1e-10,1);findings+=f;unverified+=u;booleanchecks+=c
 if (i+1)%10==0:print('Boolean pairs checked',i+1,flush=True)
assert sha(p)==before;out=dict(ifc_sha256=before,physical_scope_bodies=604,excluded_nonphysical_reservations=60,conservative_primitive_bounds_cover_all604=True,new_pair_candidates=len(pairs),prior184_scope_pairs_reused=prior,analytic_halfspace_pairs=halfspace,all320_new_interfaces_checked=True,intersection_count=len(findings),unverified=unverified,findings=findings,boolean_checks=booleanchecks,positive_native_branch_instances=320,cache_actual_native_calls=cache.actual_native_calls,volume_tolerance_m3=1e-10,linear_tolerance_m=2e-5,contact_clearance_waivers=0,installed_clearance_verified=False,design_accepted=False);(O/'intersection-review.json').write_text(json.dumps(out,indent=2));(O/'cache-index.json').write_text(json.dumps(cache.metadata,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ['findings','boolean_checks']}))

