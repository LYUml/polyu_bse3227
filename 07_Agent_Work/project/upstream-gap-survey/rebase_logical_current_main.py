"""Rebase verified downstream logical candidate on current main without moving terminals."""
import json,hashlib
from pathlib import Path
import numpy as np,ifcopenshell,ifcopenshell.api as api
from ifcopenshell.util import placement,system
from bsa.rectangular_tee_transitions import relative_placement
from bsa.duct_fitting_chain import shape_hash
B=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs');S=B/'logical-equipment-network/Supply Air Logical Network.ifc';MAIN=B/'recentered-cross-network/Supply Network.ifc';OLDMAIN=B/'equal-cross-compound-core-candidate/Supply Network.ifc';O=B/'recentered-logical-supply-network';O.mkdir(exist_ok=False)
m=ifcopenshell.open(str(S));old=ifcopenshell.open(str(S));lib=ifcopenshell.open(str(MAIN));parent=ifcopenshell.open(str(OLDMAIN));fits=json.loads((B/'recentered-cross-network/downstream-reuse-audit/adapter-fit.json').read_text())
remove=[o.GlobalId for o in parent.by_type('IfcDistributionElement') if not (o.Name.endswith('-INLET-TRANSITION') or o.Name.endswith('-ROUND-LEAD'))];assert len(remove)==124
retained={o.GlobalId:shape_hash(o) for o in m.by_type('IfcDistributionElement') if o.GlobalId not in remove};assert len(retained)==480
for g in remove:api.run('root.remove_product',m,product=m.by_guid(g))
storey=m.by_type('IfcBuildingStorey')[0];group=m.by_guid(json.loads((B/'logical-equipment-network/integration.json').read_text())['system_guid']);reuse={}
for obj in lib.by_type('IfcDistributionElement'):
 added=api.run('project.append_asset',m,library=lib,element=obj,reuse_identities=reuse,assume_asset_uniqueness_by_name=False);world=placement.get_local_placement(obj.ObjectPlacement);added.ObjectPlacement=relative_placement(m,world,None)
 for p in system.get_ports(added):p.ObjectPlacement=relative_placement(m,np.linalg.inv(world)@placement.get_local_placement(lib.by_guid(p.GlobalId).ObjectPlacement),added.ObjectPlacement)
 api.run('spatial.assign_container',m,products=[added],relating_structure=storey);api.run('system.assign_system',m,products=[added],system=group)
# Explicitly copy the validated main graph; append_asset does not authorize inferred links.
present={(r.RelatingPort.GlobalId,r.RelatedPort.GlobalId) for r in m.by_type('IfcRelConnectsPorts')}
for rel in lib.by_type('IfcRelConnectsPorts'):
 pair=(rel.RelatingPort.GlobalId,rel.RelatedPort.GlobalId)
 if pair not in present:api.run('system.connect_port',m,port1=m.by_guid(pair[0]),port2=m.by_guid(pair[1]),direction='SOURCE')
for row in fits:
 obj=m.by_guid(row['current_straight_guid']);out=m.by_guid(row['current_outlet_port']);target=m.by_guid(row['source_rectangular_port']);sf=placement.get_local_placement(obj.ObjectPlacement);frames={p.GlobalId:placement.get_local_placement(p.ObjectPlacement) for p in system.get_ports(obj)};frames[out.GlobalId][:3,3]=placement.get_local_placement(target.ObjectPlacement)[:3,3];coords=[float((f[:3,3]-sf[:3,3])@sf[:3,2]) for f in frames.values()];depth=max(coords)-min(coords);assert depth>=.08-1e-9;obj.Representation.Representations[0].Items[0].Depth=depth;sf[:3,3]+=sf[:3,2]*min(coords);obj.ObjectPlacement=relative_placement(m,sf,None)
 for p in system.get_ports(obj):p.ObjectPlacement=relative_placement(m,np.linalg.inv(sf)@frames[p.GlobalId],obj.ObjectPlacement)
 a,b=[placement.get_local_placement(p.ObjectPlacement) for p in [out,target]];assert np.allclose(a[:3,3],b[:3,3],atol=1e-8,rtol=0) and np.allclose(a[:3,2],-b[:3,2],atol=1e-8,rtol=0)
 api.run('system.connect_port',m,port1=out,port2=target,direction='SOURCE')
path=O/'Supply Air Logical Network.ifc';m.write(str(path));m=ifcopenshell.open(str(path));assert len(m.by_type('IfcDistributionElement'))==598 and len(m.by_type('IfcRelConnectsPorts'))==597
assert all(shape_hash(m.by_guid(g))==h for g,h in retained.items());trimmed={r['current_straight_guid'] for r in fits};assert all(shape_hash(m.by_guid(o.GlobalId))==shape_hash(o) for o in lib.by_type('IfcDistributionElement') if o.GlobalId not in trimmed)
record=dict(source_logical_sha256=hashlib.sha256(S.read_bytes()).hexdigest(),source_main_sha256=hashlib.sha256(MAIN.read_bytes()).hexdigest(),ifc_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),distribution_elements=598,ports=len(m.by_type('IfcDistributionPort')),interfaces=597,downstream480_shapes_unchanged=True,current98_untrimmed_main_shapes_unchanged=True,trimmed_straights=20,terminal_positions_unchanged=True,physical_airways_verified=False,full_pressure_verified=False,design_accepted=False)
(O/'integration.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
