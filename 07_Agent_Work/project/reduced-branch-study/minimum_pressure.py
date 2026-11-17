"""Given forty-percent minimum-flow scenario, reusing native analysis and tables."""
import hashlib
import json
import math
from pathlib import Path
import ifcopenshell
import ifcopenshell.util.system as system
import numpy as np
from bsa import source_network_analysis as analysis
from bsa import duct_fitting_data as tables
from bsa import duct_transition_quantities as transitions
from bsa import duct_elbow_quantities as elbows
from bsa.source_pressure_ledger import calculate as ledger

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'runs/reduced-branch-network-reviewed'
OUT=RUN/'minimum-flow'
if OUT.exists():raise ValueError('Fresh output required')
OUT.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
maximum=json.loads((RUN/'analysis.json').read_text())
brief=ROOT/'project/sources/D001/BSE3227 Mini design assignment.pdf'
assert sha(brief)=='7d97a8883fb42a08ba85e5efa76f5609f75b0e6eab9871b1f2bb8d6cd197a680'
pins={str(p):sha(p) for p in (brief,RUN/'analysis.json',RUN/'basis.json',RUN/'Supply Network.ifc',Path(__file__))}
model=ifcopenshell.open(str(RUN/'Supply Network.ifc'))
bindings={g:dict(source_section=r['source_section'],source_node=r['source_node'],flow_m3_s=r['flow_m3_s']*.4,
    classification='Derived minimum design flow: given40percent turndown applied to inherited maximum design flow') for g,r in maximum['port_flows'].items()}
minimum=analysis.calculate(model,bindings,maximum['air'])
minimum.update(air=maximum['air'],air_source_basis=maximum['air_source_basis'],original_requirement_ids=maximum['original_requirement_ids'],
    source=str(RUN),scenario='given40percentminimumflow',flow_basis=dict(source='Original brief task2,minimum turn down ratio40percent',source_sha256=sha(brief),maximum_analysis_sha256=sha(RUN/'analysis.json'),ratio=.4),
    complete_network=False)
for guid,row in minimum['port_flows'].items():
    old=maximum['port_flows'][guid]
    assert math.isclose(row['flow_m3_s'],old['flow_m3_s']*.4,rel_tol=1e-12,abs_tol=0)
    assert np.allclose([row['width_m'],row['height_m']],[old['width_m'],old['height_m']],atol=1e-8,rtol=0)
    row.update(width_m=old['width_m'],height_m=old['height_m'])
    v=row['flow_m3_s']/(row['width_m']*row['height_m'])
    row.update(actual_velocity_m_s=v,actual_velocity_pressure_Pa=minimum['air']['density_kg_m3']*v*v/2)
for obj in model.by_type('IfcDistributionElement'):
    if obj.is_a('IfcDuctSegment'):continue
    incoming=next(p for p in system.get_ports(obj) if p.FlowDirection=='SINK')
    outgoing=[p for p in system.get_ports(obj) if p.FlowDirection=='SOURCE']
    product=next(r for r in minimum['products'] if r['guid']==obj.GlobalId)
    if obj.PredefinedType=='TRANSITION':
        product['transition_geometry']=transitions.calculate(obj,incoming.Name,outgoing[0].Name)
    elif obj.PredefinedType=='BEND':
        product['elbow_geometry']=elbows.calculate(obj,incoming.Name,outgoing[0].Name,minimum['port_flows'][incoming.GlobalId]['flow_m3_s'],minimum['air'])
basis,basis_pins=tables.prepare(RUN/'basis.json')
result=tables.calculate(model,minimum,basis)
result['original_requirement_ids']=minimum['original_requirement_ids']
pressure=ledger(minimum,result)
maximum_loss=json.loads((RUN/'fitting-data.json').read_text())
key=lambda r:tuple(r[k] for k in ('product_guid','inlet_port_guid','outlet_port_guid'))
known={key(r):r for r in maximum_loss['table_results'] if r['coefficient'] is not None}
branch=next(r for r in result['table_results'] if r['coefficient'] is not None and r['citation_location'].endswith('branch Cc,b'))
assert math.isclose(branch['signed_tabulated_contribution_Pa'],known[key(branch)]['signed_tabulated_contribution_Pa']*.16,rel_tol=1e-12,abs_tol=0)
assert len(minimum['boundary_paths'])==20 and minimum['flow_continuity_pass']
assert math.isclose(minimum['boundary_inlet_flow_m3_s'],maximum['boundary_inlet_flow_m3_s']*.4,rel_tol=1e-12,abs_tol=0)
assert all(sha(Path(p))==h for p,h in {**pins,**basis_pins}.items())
for name,data in [('analysis.json',minimum),('fitting-data.json',result),('pressure-ledger.json',pressure)]:
    (OUT/name).write_text(json.dumps(data,indent=2))
receipt=dict(scenario='given40percentminimumflow',ports=len(minimum['port_flows']),outlets=len(minimum['boundary_paths']),
    inlet_flow_m3_s=minimum['boundary_inlet_flow_m3_s'],flow_continuity_pass=True,
    all_saved_port_flows_match_point4_maximum=True,elbow_reynolds_recomputed=True,
    conditional_numerical_paths=result['calculated_table_paths'],numerical_gaps=pressure['numerically_unresolved_fitting_path_count'],
    new_branch_pressure_matches_point16_maximum=True,pressure_budget_complete=False,design_accepted=False,
    inputs={**pins,**basis_pins},artifacts={name:sha(OUT/name) for name in ('analysis.json','fitting-data.json','pressure-ledger.json')},
    scope='Given minimum supply-flow scenario with inherited air properties; not actual part-load room gains, ADPI prediction, equipment control or complete pressure duty')
(OUT/'review.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps({k:v for k,v in receipt.items() if k not in ('inputs','artifacts')},indent=2))
