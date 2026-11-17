"""Rebuild all six affected tee/main-taper groups from the actual recentered plan."""
import copy
import hashlib
import json
import math
from pathlib import Path
import ezdxf
import ifcopenshell
import numpy as np
from bsa import vav_recenter as revision,duct_junction_review as junctions
from bsa import source_tee_candidates as compiler,rectangular_tee_transitions as composition
from bsa import unequal_rectangular_tee as tee,rectangular_transition as taper
from bsa.duct_transition_quantities import calculate,family_check
from bsa.duct_fitting_data import lookup

ROOT=Path('C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work')
PARENT=ROOT/'runs/vav-recenter-friction-compensated'
OUT=ROOT/'runs/recentered-local-fittings'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if OUT.exists():raise ValueError('Fresh output required')
assert revision.verify(PARENT)['integrity_pass']
schedule=json.loads((PARENT/'delivery/schedule/results.json').read_text())
new=junctions.inspect(ezdxf.readfile(PARENT/'delivery/native/reopened/source-export.dxf'),schedule,json.loads((PARENT/'inputs/binding.json').read_text()))
old=json.loads((ROOT/'runs/elbow-radius-selected/junction.json').read_text());before={n['node']:n for n in old['nodes']}
policy=json.loads((ROOT/'project/source-tee-study/policy.json').read_text())
basis=json.loads((ROOT/'project/elbow-radius-study/basis.json').read_text())
loss_basis=json.loads((ROOT/'runs/reduced-branch-network-reviewed/one-plane-source-extension-reviewed/basis.json').read_text())
families=['centred_equal_angle_pyramidal','centred_one_plane']
tables={f:copy.deepcopy(next(t for t in loss_basis['tables'] if t.get('transition_family')==f)) for f in families}
tables['centred_one_plane']['axes'][1]['values']=[15.,30.,45.]
tables['centred_one_plane']['coefficients']=[[0.,0.,0.],[.20,.20,.24]]
tables['centred_one_plane']['citation_location']+='; visually reviewed unambiguous15degree contraction column'
def signature(n):return n['point_m'],[(x['section'],x['width_m'],x['height_m']) for x in n['incidents']]
changed=[n for n in new['nodes'] if n['node'] in policy['nodes'] and signature(n)!=signature(before[n['node']])]
assert {n['node'] for n in changed}=={'TAP-VAV-04','TAP-VAV-05','TAP-VAV-10','TAP-VAV-11','TAP-VAV-16','TAP-VAV-17'}
OUT.mkdir();records=[]
for node in changed:
    name=node['node'];choice=copy.deepcopy(policy['nodes'][name])
    choice['core_section_m']=[max(x['width_m'] for x in node['incidents']),max(x['height_m'] for x in node['incidents'])]
    choice['main_half_length_m']=choice['branch_length_m']=choice['core_section_m'][0]/2+.1
    choice['source']+='; Rebased onto verified recentered plan and compensated schedule; retain original maximum-section/+0.1m core policy. No product acceptance.'
    spec,data,binding=compiler.compile_node(new,basis,name,choice)
    folder=OUT/name;folder.mkdir()
    for filename,item in [('tee.json',spec),('project.json',data),('binding.json',binding)]:
        (folder/filename).write_text(json.dumps(item,indent=2))
    _,_,_,_,children=composition.prepare(folder/'project.json')
    branch=data['arms']['branch'];assert branch['kind']=='transition'
    reduced=dict(tee=copy.deepcopy(spec),branch_section_m=branch['end_section_m'])
    reduced['tee']['branch_length_m']+=sum(branch[k] for k in ['start_length_m','transition_length_m','end_length_m'])
    request=folder/'reduced-tee.json';request.write_text(json.dumps(reduced,indent=2))
    native=tee.run(request,folder/'tee');assert tee.verify(folder/'tee')['integrity_pass']
    assert np.allclose(taper.port_frames(children['branch'])['end'],tee.base.port_frames(reduced['tee'])['branch'],atol=1e-8,rtol=0)
    main=[]
    for arm,child in children.items():
        if arm=='branch':continue
        req=folder/(arm+'.json');req.write_text(json.dumps(child,indent=2))
        result=taper.run(req,folder/arm)
        model=ifcopenshell.open(str(folder/arm/'transition.ifc'));fitting=model.by_type('IfcDuctFitting')[0]
        # Incoming arms flow from end into start; physical native orientation is retained.
        incoming='start' if child['port_directions']['start']=='SINK' else 'end'
        outgoing='end' if incoming=='start' else 'start'
        geo=calculate(fitting,incoming,outgoing)
        screens={f:family_check(f,geo) for f in families}
        quantity=dict(geo['quantities'],inlet_to_outlet_area_ratio=math.prod(geo['inlet_section_m'])/math.prod(geo['outlet_section_m']))
        queries={f:lookup(tables[f],quantity) for f in families if screens[f]['pass_check']}
        main.append(dict(arm=arm,source_section=binding['arms'][arm],geometry=geo,family_screens=screens,source_queries=queries,ifc_sha256=result['ifc_sha256']))
    assert len(main)==1
    records.append(dict(node=name,tee_source_core_section_m=choice['core_section_m'],branch_section_m=reduced['branch_section_m'],
        tee_native_checks=native['checks'],tee_ifc_sha256=native['ifc_sha256'],branch_external_plane_matches_source_composition=True,
        main_transitions=main,original_source_node=before[name],revised_source_node=node))
supported=[r['node'] for r in records if any(q['coefficient'] is not None for m in r['main_transitions'] for q in m['source_queries'].values())]
assert set(supported)=={'TAP-VAV-04','TAP-VAV-10','TAP-VAV-16'}
assert revision.verify(PARENT)['integrity_pass']
summary=dict(rebuilt_tee_groups=6,rebuilt_reduced_tees=6,rebuilt_main_transitions=6,new_source_family_candidates=supported,
    source_sizes_and_node_frames_from_recentered_plan=True,new_staged_transition_joints=0,network_integrated=False,
    current_network_numeric_gaps_unchanged=33,full_pressure_verified=False,design_accepted=False)
(OUT/'review.json').write_text(json.dumps(dict(summary=summary,cases=records,source_revision_sha256=sha(PARENT/'revision.json'),method_sha256=sha(Path(__file__))),indent=2))
print(json.dumps(summary,indent=2))
