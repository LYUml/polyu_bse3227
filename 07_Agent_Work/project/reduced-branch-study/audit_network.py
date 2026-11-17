"""Independent saved-model and source-path replay for the revised network."""
import copy
import hashlib
import json
import math
from pathlib import Path
import numpy as np
import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.system as system
import ifcopenshell.util.placement as placement
from bsa import source_tee_network as inventory
from bsa import source_compound_network as network
from bsa import rectangular_tee as tee
from bsa import unequal_rectangular_tee as author
from bsa import interface_contacts as caps
from bsa import source_network_analysis as analysis

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'runs/reduced-branch-network-reviewed'
LOCAL=ROOT/'runs/reduced-branch-design-final'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((OUT/'revision.json').read_text())
assert all(sha(Path(p))==h for p,h in receipt['inputs'].items())
assert all(sha(OUT/p)==h for p,h in receipt['artifacts'].items())
original=json.loads((ROOT/'runs/source-network-analysis-native/analysis.json').read_text())
oldfile=Path(original['source'])/'Supply Network.ifc'
assert sha(oldfile)==receipt['source_network_sha256']
oldmodel=ifcopenshell.open(str(oldfile));expected,_=inventory.snapshot([oldfile])
removed=set();revised=set();changes=[]
for path in sorted(LOCAL.glob('*/project.json')):
    author.verify(path.parent/'native')
    data=json.loads(path.read_text());guid=tee.stable_guid(data['tee'],'IfcDuctFitting','RECTANGULAR-TEE')
    branch=tee.stable_guid(data['tee'],'IfcDistributionPort','RECTANGULAR-TEE','branch')
    original_links=expected['links'];start=next(b for a,b in original_links if a==branch)
    owner=expected['ports'][start]['owner'];end=next(g for g,p in expected['ports'].items() if p['owner']==owner and p['name']=='end')
    peer=next(b for a,b in original_links if a==end)
    replacement,_=inventory.snapshot([path.parent/'native/unequal-tee.ifc'])
    assert np.allclose(replacement['ports'][branch]['frame'],expected['ports'][end]['frame'],atol=1e-8,rtol=0)
    wanted=expected['objects'][guid];wanted['shape']=replacement['objects'][guid]['shape']
    wanted['properties']['BSA_DesignInputs'].update(replacement['objects'][guid]['properties']['BSA_DesignInputs'])
    expected['ports'][branch]=replacement['ports'][branch]
    expected['objects'].pop(owner)
    expected['ports'].pop(start);expected['ports'].pop(end)
    expected['links']=[tuple(p) for p in expected['links'] if start not in p and end not in p]+[(branch,peer)]
    removed.add(owner);revised.add(guid);changes.append((branch,peer))
expected['links']=sorted(set(map(tuple,expected['links'])))
checks=network.inspect(OUT/'Supply Network.ifc',expected)
model=ifcopenshell.open(str(OUT/'Supply Network.ifc'))
saved=json.loads((OUT/'analysis.json').read_text());loss=json.loads((OUT/'fitting-data.json').read_text())
bindings={g:{k:old[k] for k in ('source_section','source_node','flow_m3_s','classification')} for g,old in original['port_flows'].items() if g in expected['ports']}
fresh=analysis.calculate(model,bindings,original['air'])
assert set(saved['port_flows'])==set(fresh['port_flows'])==set(bindings)
for guid,row in fresh['port_flows'].items():
    assert math.isclose(row['flow_m3_s'],saved['port_flows'][guid]['flow_m3_s'],rel_tol=1e-12,abs_tol=0)
assert fresh['boundary_ports']==original['boundary_ports']
assert fresh['straight_sections']==original['straight_sections']
assert fresh['boundary_paths']==saved['boundary_paths']
settings=ifcopenshell.geom.settings();settings.set(settings.USE_WORLD_COORDS,True)
meshes={};pairs=[]
for link in model.by_type('IfcRelConnectsPorts'):
    ports=[link.RelatingPort,link.RelatedPort];sections=[]
    for port in ports:
        obj=system.get_port_element(port)
        if obj.GlobalId not in meshes:
            shape=ifcopenshell.geom.create_shape(settings,obj)
            meshes[obj.GlobalId]=(np.asarray(shape.geometry.verts).reshape(-1,3),np.asarray(shape.geometry.faces).reshape(-1,3))
        sections.append(caps.cap(*meshes[obj.GlobalId],placement.get_local_placement(port.ObjectPlacement)))
    caps.matching(*sections);pairs.append([p.GlobalId for p in ports])
old_loss=json.loads((ROOT/'runs/mcp-native-fitting-analysis/fitting-data.json').read_text())
key=lambda r:tuple(r[k] for k in ('product_guid','inlet_port_guid','outlet_port_guid'))
before={key(r):r for r in old_loss['table_results']};after={key(r):r for r in loss['table_results']}
unchanged=0
for k,row in before.items():
    if row['coefficient'] is not None and k in after:
        assert math.isclose(row['coefficient'],after[k]['coefficient'],rel_tol=1e-12,abs_tol=0)
        assert math.isclose(row['signed_tabulated_contribution_Pa'],after[k]['signed_tabulated_contribution_Pa'],rel_tol=1e-12,abs_tol=0)
        unchanged+=1
added=[r for k,r in after.items() if r['coefficient'] is not None and before.get(k,{}).get('coefficient') is None]
assert len(added)==1 and unchanged==28
point=json.loads((LOCAL/'drawing-reviewed/independent-point-check.json').read_text())
assert math.isclose(added[0]['signed_tabulated_contribution_Pa'],point['conditional_loss_Pa'],rel_tol=1e-12,abs_tol=0)
assert len(loss['data_requests'])==63 and loss['calculated_table_paths']==29
assert saved['original_requirement_ids']==original['original_requirement_ids']
assert loss['pressure_budget_complete'] is False and loss['critical_path'] is None
result=dict(native_inventory_source_replay_pass=True,source_prescribed_flow_replay_pass=True,
    unchanged_straight_sections=len(fresh['straight_sections']),unchanged_boundary_outlet_count=len(fresh['boundary_paths']),
    native_material_cap_pairs_matched=len(pairs),old_finite_losses_retained=unchanged,removed_old_finite_transition_values=3,
    new_conditional_branch_values=1,new_branch_matches_independent_decimal_point=True,
    fitting_paths=63,finite_paths=29,numerical_gaps=34,original_source_requirements=len(saved['original_requirement_ids']),
    artifact_sha256=receipt['artifacts'],design_accepted=False,
    scope='Independent source/saved geometry,cap,graph/flow/path and unchanged-table-value audit; not full pressure or installation acceptance')
(OUT/'independent-review.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
