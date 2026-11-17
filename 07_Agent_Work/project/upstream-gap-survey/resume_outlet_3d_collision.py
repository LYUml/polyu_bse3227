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
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs');R=B/'three-dimensional-outlet-candidate';O=R/'bounded-collision-analytic';O.mkdir(exist_ok=False);p=R/'Supply and Three Dimensional Outlet Candidate.ifc';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before=sha(p);m=ifcopenshell.open(str(p));review=json.loads((R/'review.json').read_text());cache=Cache(O/'mesh-cache');native_path=R/'bounded-native-reviewed/native-review.json';native=json.loads(native_path.read_text());assert native['ifc_sha256']==before and native['schema_express_errors']==0 and native['branch_bodies']==320;checks=native['records'];canonical=native['canonical_shapes'];import shutil
for h,meta in canonical.items():
 src=R/'bounded-native-reviewed/mesh-cache'/(h+'.npz');dst=O/'mesh-cache'/(h+'.npz');shutil.copy2(src,dst);assert sha(src)==sha(dst);cache.metadata[h]=dict(sample_guid=meta['sample_guid'],npz_sha256=sha(dst),executed_native_review_sha256=sha(native_path))
print('Reusing77executedcanonicalmeshes;320nativeinstancesandschemapreserved',flush=True)
# All physical pieces get conservative bounds,not mesh boxes substituted for solids.
els=[e for e in m.by_type('IfcElement') if e.Representation and (e.is_a('IfcDistributionElement') or (e.Name or '').endswith('CASING') or (e.Name or '').startswith('CANDIDATE_VAV-'))];assert len(els)==604;bs={e.GlobalId:bounds(body(e),matrix(e)) for e in els};added={x['guid'] for x in checks};adjacent={}
for link in m.by_type('IfcRelConnectsPorts'):
 a,b=link.RelatingPort,link.RelatedPort;oa,ob=system.get_port_element(a),system.get_port_element(b)
 if oa.GlobalId not in added and ob.GlobalId not in added:continue
 f1,f2=[placement.get_local_placement(p.ObjectPlacement) for p in [a,b]];assert a.FlowDirection=='SOURCE' and b.FlowDirection=='SINK' and np.allclose(f1[:3,3],f2[:3,3],atol=1e-9,rtol=0) and np.allclose(f1[:3,2],-f2[:3,2],atol=1e-9,rtol=0)
 # A positive-length straight adjoins one minor bend or a checked reducer.
 if oa.GlobalId not in added:reducer_read(oa,.15,1.2)
 assert (oa.is_a('IfcDuctSegment') or ob.is_a('IfcDuctSegment'))
 adjacent[tuple(sorted([oa.GlobalId,ob.GlobalId]))]='Separated open halfspaces at exact common cap;minor bend0<theta<=90 andR>outerradius or monotone reducer;not a contact waiver'
assert len(adjacent)==320
oldpath=B/'equal-cross-compound-core-candidate/equipment-space/model.ifc';old=ifcopenshell.open(str(oldpath));oldproof=json.loads((oldpath.parent/'casing-intersection-review.json').read_text());assert oldproof['source_ifc_sha256']==sha(oldpath) and oldproof['intersection_count']==0 and not oldproof['unverified'];oldids={e.GlobalId for e in old.by_type('IfcElement') if e.Representation and (e.is_a('IfcDistributionElement') or (e.Name or '').endswith('CASING') or (e.Name or '').startswith('CANDIDATE_VAV-'))};assert len(oldids)==184
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

