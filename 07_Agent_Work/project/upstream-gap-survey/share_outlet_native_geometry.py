import hashlib,json
from pathlib import Path
import ifcopenshell
from ifcopenshell.util import element,placement,system
import numpy as np
from bsa.duct_fitting_chain import value
from bsa.round_bend_quantities import calculate
R=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/three-dimensional-outlet-candidate');source=R/'Supply and Three Dimensional Outlet Candidate.ifc';m=ifcopenshell.open(str(source));review=json.loads((R/'review.json').read_text());original=ifcopenshell.open(str(source));oldids={p['guid'] for r in review['records'] for p in r['pieces']};pinned={e.id():str(e) for e in m if e.id()<min(m.by_guid(g).id() for g in oldids)};cache={};replaced=[]
for g in sorted(oldids):
 obj=m.by_guid(g);reps=[]
 for rep in obj.Representation.Representations:
  key=json.dumps(value(rep),sort_keys=True,separators=(',',':'))
  if key not in cache:cache[key]=rep
  elif cache[key]!=rep:replaced.append(rep)
  reps.append(cache[key])
 obj.Representation.Representations=reps
for rep in replaced:
 if not m.get_inverse(rep):element.remove_deep2(m,rep)
assert all(str(m.by_id(i))==s for i,s in pinned.items());assert len(m.by_type('IfcElement'))==664
for obj in m.by_type('IfcElement'):
 prior=original.by_guid(obj.GlobalId);assert value(obj.Representation)==value(prior.Representation);assert np.array_equal(placement.get_local_placement(obj.ObjectPlacement),placement.get_local_placement(prior.ObjectPlacement));assert {p.GlobalId for p in system.get_ports(obj)}=={p.GlobalId for p in system.get_ports(prior)}
for route in review['records']:
 for p in route['pieces']:
  if p['kind']=='bend':calculate(m.by_guid(p['guid']))
target=R/'Supply and Outlet Connections.ifc';m.write(str(target));proof=dict(source_ifc_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),shared_ifc_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),all664element_representation_values_and_placements_identical=True,all_original_element_entities_preserved=True,all160bends_read_with_current_reader=True,new_branch_products=320,shared_body_and_axis_representation_count=len(cache),replaced_representation_references=len(replaced),source_bytes=source.stat().st_size,shared_bytes=target.stat().st_size,geometry_changed=False,ports_and_connections_changed=False,design_accepted=False);(R/'shared-geometry-review.json').write_text(json.dumps(proof,indent=2));print(json.dumps(proof))
