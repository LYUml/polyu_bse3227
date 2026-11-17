import json,hashlib
from pathlib import Path
import ifcopenshell,ifcopenshell.geom
from bsa.solid_clash import overlaps
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/constant-height-tee-network');p=B/'equipment-space/model.ifc';m=ifcopenshell.open(str(p));els=[e for e in m.by_type('IfcElement') if e.Representation and (e.is_a('IfcDistributionElement') or e.Name.endswith('CASING') or e.Name.startswith('CANDIDATE_VAV-'))];assert len(els)==165
s=ifcopenshell.geom.settings();s.set(s.USE_WORLD_COORDS,True);meshes={}
for e in els:
 shape=ifcopenshell.geom.create_shape(s,e);g=shape.geometry;meshes[e.GlobalId]=(list(g.verts),list(g.faces))
f,u,n,c=overlaps(els,meshes,2e-5,1e-10,5000)
x=dict(source_ifc_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),physical_scope_bodies=165,excluded_nonphysical_reservations=60,intersection_count=len(f),unverified=u,boolean_candidates=n,findings=f,design_accepted=False);(B/'equipment-space/casing-intersection-review.json').write_text(json.dumps(x,indent=2));print(json.dumps(x))

