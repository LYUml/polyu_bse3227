import json,hashlib
from pathlib import Path
import numpy as np,ifcopenshell,ifcopenshell.geom,ifcopenshell.validate
from ifcopenshell.util import placement,system
from outlet_native_batches import bounds,body,matrix
R=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs/three-dimensional-outlet-candidate');p=R/'Shared Supply and Outlet Connections.ifc';m=ifcopenshell.open(str(p));old=ifcopenshell.open(str(R/'Supply and Three Dimensional Outlet Candidate.ifc'));n=0
for port in m.by_type('IfcDistributionPort'):
 a=old.by_guid(port.GlobalId);assert port.Name==a.Name and port.FlowDirection==a.FlowDirection and system.get_port_element(port).GlobalId==system.get_port_element(a).GlobalId;assert np.array_equal(placement.get_local_placement(port.ObjectPlacement),placement.get_local_placement(a.ObjectPlacement));n+=1
assert n==1147;links=lambda f:{r.GlobalId:(r.RelatingPort.GlobalId,r.RelatedPort.GlobalId) for r in f.by_type('IfcRelConnectsPorts')};assert links(m)==links(old) and len(links(m))==483
s=ifcopenshell.geom.settings();s.set(s.USE_WORLD_COORDS,True);records=[]
for o in m.by_type('IfcElement'):
 if not o.Representation or not body(o).is_a('IfcMappedItem'):continue
 shape=ifcopenshell.geom.create_shape(s,o);v=np.asarray(shape.geometry.verts).reshape(-1,3);lo,hi=bounds(body(o),matrix(o));assert np.all(v.min(axis=0)>=lo-1e-8) and np.all(v.max(axis=0)<=hi+1e-8);records.append(o.GlobalId)
print('All',len(records),'mapped native meshes enclosed;1147ports/483links unchanged',flush=True)
log=ifcopenshell.validate.json_logger();ifcopenshell.validate.validate(m,log,express_rules=True);assert not log.statements;proof=dict(ifc_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),source_ifc_sha256=hashlib.sha256((R/'Supply and Three Dimensional Outlet Candidate.ifc').read_bytes()).hexdigest(),all1147port_world_frames_names_directions_and_owners_preserved=True,all483connections_preserved=True,native_mapped_instance_bounds_checked=len(records),native_mapped_instance_guids=records,schema_express_errors=0,geometry_sharing_handoff=hashlib.sha256((R/'shared-product-shape-review.json').read_bytes()).hexdigest(),collision_evidence_source_sha256=hashlib.sha256((R/'bounded-collision-analytic/intersection-review.json').read_bytes()).hexdigest(),collision_reuse_basis='All664nativegeometryvaluesandworldplacementsidentical;portandlinkidentityreconciled. Originalcollisionchecknotrelabelled asfresh shared-modelmeshing.',bounds_helper_sha256=hashlib.sha256(Path(__file__).with_name('outlet_native_batches.py').read_bytes()).hexdigest(),design_accepted=False);(R/'shared-product-shape-acceptance.json').write_text(json.dumps(proof,indent=2));print('Shared IFC schema EXPRESS pass')
