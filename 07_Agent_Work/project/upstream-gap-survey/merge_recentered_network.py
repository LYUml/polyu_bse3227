"""Rebase saved network using verified local replacements and current source graph."""
import copy
import hashlib
import json
import math
from pathlib import Path
import numpy as np
import ifcopenshell
import ifcopenshell.api as api
from ifcopenshell.util import placement,system,element
from bsa.rectangular_tee_transitions import relative_placement
from bsa import source_tee_network as inventory,source_compound_network as network,source_network_analysis as analysis
from bsa.duct_fitting_chain import shape_hash,properties

ROOT=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work')
OLD=ROOT/'runs/reduced-branch-network-reviewed'
LOCAL=ROOT/'runs/recentered-local-fittings'
PLAN=ROOT/'runs/vav-recenter-friction-compensated'
OUT=ROOT/'runs/recentered-network-integrated'
if OUT.exists():raise ValueError('Fresh output required')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=OLD/'Supply Network.ifc';before=sha(source)
model=ifcopenshell.open(str(source));expected,_=inventory.snapshot([source])
case=json.loads((OLD/'analysis.json').read_text())
local=json.loads((LOCAL/'review.json').read_text())
assert sha(PLAN/'revision.json')==local['source_revision_sha256']
newnodes={n['node']:n for n in json.loads((ROOT/'runs/recentered-vav-connection-schedule/revised-junction.json').read_text())['nodes']}
oldnodes={n['node']:n for n in json.loads((ROOT/'runs/elbow-radius-selected/junction.json').read_text())['nodes']}
schedule={r['id']:r['inputs'] for r in json.loads((PLAN/'delivery/schedule/results.json').read_text())['sections']}
tree={r['id']:r for r in json.loads((PLAN/'inputs/ducts.json').read_text())['tree']['sections']}
peer={}
for a,b in expected['links']:peer[a]=b;peer[b]=a
changes=[]
def frames(obj):return {p.GlobalId:placement.get_local_placement(p.ObjectPlacement) for p in system.get_ports(obj)}
def position(obj,world,world_ports):
    obj.ObjectPlacement=relative_placement(model,world,None)
    for p in system.get_ports(obj):p.ObjectPlacement=relative_placement(model,np.linalg.inv(world)@world_ports[p.GlobalId],obj.ObjectPlacement)
def update_props(obj,values):
    pset=next(r.RelatingPropertyDefinition for r in obj.IsDefinedBy if r.RelatingPropertyDefinition.Name=='BSA_DesignInputs')
    api.run('pset.edit_pset',model,pset=pset,properties=copy.deepcopy(values))
for item in local['cases']:
    folder=LOCAL/item['node']
    for path in [folder/'tee/unequal-tee.ifc',*[folder/t['arm']/'transition.ifc' for t in item['main_transitions']]]:
        replacement=ifcopenshell.open(str(path));other=replacement.by_type('IfcDuctFitting')[0]
        obj=model.by_guid(other.GlobalId);assert {p.GlobalId for p in system.get_ports(obj)}=={p.GlobalId for p in system.get_ports(other)}
        rep=obj.Representation.Representations[0];incoming=other.Representation.Representations[0]
        rep.Items=tuple(element.copy_deep(model,item) for item in incoming.Items)
        rep.RepresentationIdentifier=incoming.RepresentationIdentifier
        rep.RepresentationType=incoming.RepresentationType
        position(obj,placement.get_local_placement(other.ObjectPlacement),frames(other))
        update_props(obj,properties(other)['BSA_DesignInputs'])
        expected['objects'][obj.GlobalId].update(shape=shape_hash(other),frame=placement.get_local_placement(other.ObjectPlacement).tolist(),properties=properties(obj))
        for p in system.get_ports(other):expected['ports'][p.GlobalId]['frame']=placement.get_local_placement(p.ObjectPlacement).tolist()
        changes.append(dict(kind='source_native_replacement',guid=obj.GlobalId,node=item['node'],source=str(path),sha256=sha(path)))
moved=[]
for obj in model.by_type('IfcDuctFitting'):
    if obj.PredefinedType!='BEND':continue
    node=element.get_psets(obj)['BSA_DesignInputs']['SourceNode']
    delta=np.array(newnodes[node]['point_m'])-np.array(oldnodes[node]['point_m'])
    if np.linalg.norm(delta)<1e-8:continue
    world=placement.get_local_placement(obj.ObjectPlacement);world[:3,3]+=delta
    points=frames(obj)
    for p in points.values():p[:3,3]+=delta
    position(obj,world,points)
    expected['objects'][obj.GlobalId]['frame']=world.tolist()
    for guid,frame in points.items():expected['ports'][guid]['frame']=frame.tolist()
    moved.append(dict(node=node,guid=obj.GlobalId,delta_m=delta.tolist()))
assert len(changes)==12 and len(moved)==3
straights=[]
for obj in model.by_type('IfcDuctSegment'):
    oldprops=element.get_psets(obj)['BSA_DesignInputs'];sid=oldprops['SourceSectionID'];spec=schedule[sid]
    world=placement.get_local_placement(obj.ObjectPlacement);ports=system.get_ports(obj);points=frames(obj);wanted={}
    for p in ports:
        if p.GlobalId in peer:
            neighbour=model.by_guid(peer[p.GlobalId]);assert not system.get_port_element(neighbour).is_a('IfcDuctSegment')
            wanted[p.GlobalId]=placement.get_local_placement(neighbour.ObjectPlacement)[:3,3]
        else:
            role='from' if p.FlowDirection=='SINK' else 'to'
            wanted[p.GlobalId]=np.array(newnodes[tree[sid][role]]['point_m'])
    assert len(ports)==2
    near,far=sorted(ports,key=lambda p:float(np.dot(points[p.GlobalId][:3,3]-world[:3,3],world[:3,2])))
    delta=wanted[far.GlobalId]-wanted[near.GlobalId];length=float(np.dot(delta,world[:3,2]))
    assert length>.08 and np.allclose(delta,length*world[:3,2],atol=1e-8,rtol=0)
    world[:3,3]=wanted[near.GlobalId]
    for guid,frame in points.items():frame[:3,3]=wanted[guid]
    position(obj,world,points)
    solid=obj.Representation.Representations[0].Items[0]
    assert solid.is_a('IfcExtrudedAreaSolid') and solid.SweptArea.is_a('IfcRectangleHollowProfileDef')
    profile=element.copy_deep(model,solid.SweptArea);solid.SweptArea=profile
    w,h=spec['width_m'],spec['height_m'];profile.XDim=w+2*profile.WallThickness;profile.YDim=h+2*profile.WallThickness;solid.Depth=length
    update_props(obj,dict(InternalWidth_m=w,InternalHeight_m=h,StudyStraightLength_m=length,
        SourceCentrelineLength_m=math.dist(newnodes[tree[sid]['from']]['point_m'],newnodes[tree[sid]['to']]['point_m']),
        RevisionBasis='Actual recentered native plan and compensated schedule; fitting-trimmed finite straight; source construction assumptions remain'))
    expected['objects'][obj.GlobalId].update(shape=shape_hash(obj),frame=world.tolist(),properties=properties(obj))
    for guid,frame in points.items():expected['ports'][guid]['frame']=frame.tolist()
    straights.append(dict(guid=obj.GlobalId,section=sid,length_m=length,clear_section_m=[w,h],expected_port_frames={g:f.tolist() for g,f in points.items()}))
assert len(straights)==45
OUT.mkdir();target=OUT/'Supply Network.ifc';model.write(str(target))
checks=network.inspect(target,expected)
bindings={g:{k:r[k] for k in ['source_section','source_node','flow_m3_s','classification']} for g,r in case['port_flows'].items()}
saved=ifcopenshell.open(str(target));fresh=analysis.calculate(saved,bindings,case['air'])
assert fresh['flow_continuity_pass'] and len(fresh['boundary_paths'])==20
assert fresh['boundary_ports']==case['boundary_ports']
assert sha(source)==before
fresh.update(source=str(OUT),air=case['air'],air_source_basis=case['air_source_basis'],original_requirement_ids=case['original_requirement_ids'],complete_network=False)
(OUT/'analysis.json').write_text(json.dumps(fresh,indent=2))
(OUT/'expected.json').write_text(json.dumps(expected,indent=2))
receipt=dict(source_ifc_sha256=before,source_recenter_revision_sha256=sha(PLAN/'revision.json'),local_revision_sha256=sha(LOCAL/'review.json'),
    native_checks=checks,replacements=changes,moved_elbows=moved,straights=straights,
    original_requirements=len(case['original_requirement_ids']),network_integrated=True,full_pressure_verified=False,design_accepted=False)
(OUT/'revision.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps(dict(native_checks=checks,straight_count=45,replaced_fittings=12,moved_elbows=3,outlets=20,network_integrated=True,full_pressure_verified=False),indent=2))
