"""Integrate checked inlet assemblies by trimming actual existing leaf ducts."""
import copy,hashlib,json
from pathlib import Path
import numpy as np
import ifcopenshell
import ifcopenshell.api as api
from ifcopenshell.util import placement,system,element
from bsa import source_tee_network as inventory,source_compound_network as graph
from bsa.rectangular_tee_transitions import relative_placement

BASE=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/runs')
PARENT=BASE/'recentered-network-integrated/Supply Network.ifc'
LOCAL=BASE/'rect-round-sourced-design/analytic-inlet-assemblies'
OUT=BASE/'sourced-inlet-network';assert not OUT.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record=json.loads((LOCAL/'author-review.json').read_text())
assert sha(PARENT)==record['source_ifc_sha256']
assert sha(LOCAL/'VAV Inlet Assemblies.ifc')==record['ifc_sha256']
expected,libraries=inventory.snapshot([PARENT,LOCAL/'VAV Inlet Assemblies.ifc'])
model,library=libraries;source_sha=sha(PARENT)
changes=[];external=[]
for row in record['cases']:
    obj=model.by_guid(row['source_section_guid'])
    frame=placement.get_local_placement(obj.ObjectPlacement)
    ports=system.get_ports(obj);assert len(ports)==2
    worlds={p.GlobalId:placement.get_local_placement(p.ObjectPlacement) for p in ports}
    outlet=next(p for p in ports if p.FlowDirection=='SOURCE')
    assert not any(outlet.GlobalId in pair for pair in expected['links'])
    worlds[outlet.GlobalId][:3,3]=np.array(row['ports']['rectangle']['frame'])[:3,3]
    ordered=sorted(ports,key=lambda p:float(np.dot(worlds[p.GlobalId][:3,3],frame[:3,2])))
    near,far=[worlds[p.GlobalId][:3,3] for p in ordered]
    length=float(np.dot(far-near,frame[:3,2]));assert length>=.08-1e-9
    assert np.allclose(far-near,length*frame[:3,2],atol=1e-9,rtol=0)
    frame[:3,3]=near
    obj.ObjectPlacement=relative_placement(model,frame,None)
    for p in ports:p.ObjectPlacement=relative_placement(model,np.linalg.inv(frame)@worlds[p.GlobalId],obj.ObjectPlacement)
    solid=obj.Representation.Representations[0].Items[0];old_length=solid.Depth;solid.Depth=length
    props=element.get_psets(obj)['BSA_DesignInputs'];props['StudyStraightLength_m']=length
    pset=next(r.RelatingPropertyDefinition for r in obj.IsDefinedBy if r.RelatingPropertyDefinition.Name=='BSA_DesignInputs')
    api.run('pset.edit_pset',model,pset=pset,properties=copy.deepcopy(props))
    changes.append(dict(id=row['id'],guid=obj.GlobalId,old_length_m=old_length,new_length_m=length))
    external.append((outlet.GlobalId,row['ports']['rectangle']['guid']))
# Refresh only explicitly changed expected parent records; all other source
# bodies and local shapes remain bound to their original saved snapshots.
OUT.mkdir();trimmed=OUT/'trimmed-source.ifc';model.write(str(trimmed))
fresh,_=inventory.snapshot([trimmed])
for change in changes:
    guid=change['guid'];expected['objects'][guid]=fresh['objects'][guid]
    for p in system.get_ports(model.by_guid(guid)):expected['ports'][p.GlobalId]=fresh['ports'][p.GlobalId]
storey=model.by_type('IfcBuildingStorey')[0];group=model.by_type('IfcDistributionSystem')[0]
reuse={}
for obj in library.by_type('IfcDistributionElement'):
    added=api.run('project.append_asset',model,library=library,element=obj,reuse_identities=reuse,assume_asset_uniqueness_by_name=False)
    world=np.array(expected['objects'][obj.GlobalId]['frame']);added.ObjectPlacement=relative_placement(model,world,None)
    for port in system.get_ports(added):port.ObjectPlacement=relative_placement(model,np.linalg.inv(world)@np.array(expected['ports'][port.GlobalId]['frame']),added.ObjectPlacement)
    api.run('spatial.assign_container',model,products=[added],relating_structure=storey)
    api.run('system.assign_system',model,products=[added],system=group)
expected['links']=sorted(set(map(tuple,expected['links']))|set(external))
present={(r.RelatingPort.GlobalId,r.RelatedPort.GlobalId) for r in model.by_type('IfcRelConnectsPorts')}
for a,b in expected['links']:
    if (a,b) not in present:api.run('system.connect_port',model,port1=model.by_guid(a),port2=model.by_guid(b),direction='SOURCE')
target=OUT/'Supply Network.ifc';model.write(str(target))
check=graph.inspect(target,expected)
assert len(expected['objects'])==129 and len(expected['ports'])==277 and len(expected['links'])==128
assert sha(PARENT)==source_sha
(OUT/'expected.json').write_text(json.dumps(expected,indent=2))
(OUT/'integration.json').write_text(json.dumps(dict(source_sha256=source_sha,local_ifc_sha256=record['ifc_sha256'],
    ifc_sha256=sha(target),changes=changes,checks=check,bodies=129,ports=277,links=128,
    design_accepted=False,full_pressure_verified=False),indent=2))
print(json.dumps(dict(bodies=129,ports=277,links=128,trimmed_rectangles=len(changes),native_graph_checks=check)))
