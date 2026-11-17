"""Private source-linked local branch construction study; no parent network edit."""
import copy
import hashlib
import json
import math
from pathlib import Path
import numpy as np
import ifcopenshell
import ifcopenshell.util.placement as placement
import ifcopenshell.util.system as system
from bsa import rectangular_tee as tee
from bsa import unequal_rectangular_tee as author
from bsa.duct_fitting_data import lookup

ROOT = Path(__file__).resolve().parents[2]
PARENT = ROOT/'runs/source-tee-candidates'
ANALYSIS = ROOT/'runs/mcp-native-fitting-analysis/fitting-data.json'
OUT = ROOT/'runs/reduced-branch-design-final'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
if OUT.exists():
    raise ValueError('Fresh output required')
source = json.loads(ANALYSIS.read_text())
for name, expected in source['inputs'].items():
    if sha(Path(name)) != expected:
        raise ValueError('Parent source/method changed: '+name)
tables = json.loads((ROOT/'project/full-network-transition-study/basis.json').read_text())
branch_tables = {x['product_guid']:x for x in tables['tables'] if x['citation_location']=='Printed page42,Fitting5-28,branch Cc,b'}
old_results = {x['product_guid']:x for x in source['table_results'] if x['citation_location']=='Printed page42,Fitting5-28,branch Cc,b'}
OUT.mkdir(parents=True)
rows = []; pins = {str(ANALYSIS):sha(ANALYSIS), str(Path(__file__)):sha(Path(__file__))}
for path in sorted((PARENT/'inputs').glob('*/tee.json')):
    spec = json.loads(path.read_text()); guid = tee.stable_guid(spec, 'IfcDuctFitting', 'RECTANGULAR-TEE')
    if guid not in branch_tables:
        continue
    project = path.with_name('project.json'); binding = path.with_name('binding.json')
    composition = json.loads(project.read_text()); node = json.loads(binding.read_text())['node']
    arm = composition['arms']['branch']
    if arm['kind'] != 'transition' or spec['port_directions']['branch'] != 'SOURCE':
        raise ValueError('Original divergent branch/transition required')
    previous_native = PARENT/'models'/path.parent.name/'branch/transition.ifc'
    old_model = ifcopenshell.open(str(previous_native))
    transition = old_model.by_type('IfcDuctFitting')[0]
    end = next(p for p in system.get_ports(transition) if p.Name == 'end')
    old_frame = placement.get_local_placement(end.ObjectPlacement)
    data = dict(tee=copy.deepcopy(spec), branch_section_m=arm['end_section_m'])
    removed_length = arm['start_length_m']+arm['transition_length_m']+arm['end_length_m']
    data['tee']['branch_length_m'] += removed_length
    data['tee']['source'] += '; Separate reduced-branch study: inherit existing scheduled branch section and original external endpoint; replace the enlarged branch plus taper with one sharp reduced branch. Assumed construction, not a product or installed geometry.'
    expected = tee.port_frames(data['tee'])['branch']
    if not np.allclose(old_frame, expected, atol=1e-8, rtol=0):
        raise ValueError('Original external branch end frame changed')
    child = OUT/node; child.mkdir()
    request = child/'project.json'; request.write_text(json.dumps(data, indent=2))
    result = author.run(request, child/'native')
    if not author.verify(child/'native')['integrity_pass']:
        raise ValueError('Native saved verification failed')
    q = old_results[guid]['native_quantities'].copy()
    ratio = math.prod(arm['end_section_m'])/(spec['internal_width_m']*spec['internal_height_m'])
    q.update(outlet_to_inlet_area_ratio=ratio, inlet_to_outlet_area_ratio=1/ratio,
             outlet_to_inlet_width_ratio=arm['end_section_m'][0]/spec['internal_width_m'],
             outlet_to_inlet_height_ratio=arm['end_section_m'][1]/spec['internal_height_m'],
             outlet_to_inlet_velocity_ratio=q['outlet_to_inlet_flow_ratio']/ratio,
             outlet_aspect_ratio=arm['end_section_m'][0]/arm['end_section_m'][1])
    query = lookup(branch_tables[guid], q)
    for original in (path, project, binding, previous_native):
        pins[str(original)] = sha(original)
    rows.append(dict(node=node, branch_section_m=data['branch_section_m'], original_core_section_m=[spec['internal_width_m'], spec['internal_height_m']],
        original_external_endpoint_preserved=True, main_core_frames_preserved=True,
        removed_separate_transition_length_m=removed_length, native_checks=result['checks'],
        native_result=str(child/'native/result.json'), native_ifc_sha256=result['ifc_sha256'],
        original_query_status=old_results[guid]['status'], revised_query=query,
        signed_conditional_loss_Pa=None if query['coefficient'] is None else query['coefficient']*old_results[guid]['reference_velocity_pressure_Pa'],
        full_pressure_verified=False, physical_applicability_verified=False))
assert len(rows)==13
for name, expected in pins.items():
    if sha(Path(name)) != expected:
        raise ValueError('Input changed during run')
summary = dict(inputs=pins, cases=rows, candidate_count=len(rows), branch_transitions_removed_in_local_candidates=len(rows),
    complete_parent_network_modified=False, original_requirement_ids=source['original_requirement_ids'],
    conditional_branch_values=sum(x['revised_query']['coefficient'] is not None for x in rows),
    original_source_pressure_gaps_remain=45, design_accepted=False,
    scope='Isolated source-linked geometry revisions preserve branch external and core main end frames. Main-arm transitions remain in original models. No whole-network merge, collision, full pressure, CAD or installation acceptance.')
(OUT/'study.json').write_text(json.dumps(summary, indent=2))
print(json.dumps({k:v for k,v in summary.items() if k not in ('inputs','cases','original_requirement_ids')},indent=2))
