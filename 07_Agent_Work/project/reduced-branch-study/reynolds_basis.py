"""Extend one plateau-only source binding using the reviewed published Re grid."""
import copy
from decimal import Decimal as D
import hashlib
import json
import math
from pathlib import Path
import ifcopenshell
from bsa.duct_fitting_data import prepare,calculate
from bsa.source_pressure_ledger import calculate as ledger

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'runs/reduced-branch-network-reviewed'
OUT=RUN/'reynolds-source-extension'
if OUT.exists():raise ValueError('Fresh output required')
OUT.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
basis=json.loads((RUN/'basis.json').read_text())
guid='32SL8_FtLLxRDkUZc7lzNQ'
target=next(t for t in basis['tables'] if t['product_guid']==guid)
assert [a['quantity'] for a in target['axes']]==['bend_radius_over_radial_width','bend_height_over_radial_width']
condition=next(c for c in target['conditions'] if c['quantity']=='bend_hydraulic_reynolds')
assert condition['minimum']==200000 and condition['maximum']==100000000
assert any(c['quantity']=='bend_radius_over_radial_width' and c['minimum']==.75 for c in target['conditions'])
# Original ASHRAE2021 printed12 was rendered and individually inspected.
# Private table data only; r/W>=.75 row and the existing declared high-Re bound.
re=[10000,20000,30000,40000,60000,80000,100000,140000,200000,100000000]
factor=[2.,1.77,1.64,1.56,1.46,1.38,1.30,1.15,1.,1.]
target['axes'].append(dict(quantity='bend_hydraulic_reynolds',values=re))
target['coefficients']=[[[value*k for k in factor] for value in row] for row in target['coefficients']]
condition['minimum']=10000
target['applicability_note']+='; Explicit source extension: previously this binding represented only the >=200000 plateau needed by maximum flow. The same printed12 published10000..200000 r/W>=.75 correction row now supplies the minimum-flow case, with no extrapolation. The1e8 numerical upper study bound is unchanged and is not a published maximum.'
path=OUT/'basis.json';path.write_text(json.dumps(basis,indent=2))
prepared,pins=prepare(path)
model=ifcopenshell.open(str(RUN/'Supply Network.ifc'))
summary={};new_values={}
for name,folder in [('maximum',RUN),('minimum',RUN/'minimum-flow')]:
    case=json.loads((folder/'analysis.json').read_text());old=json.loads((folder/'fitting-data.json').read_text())
    result=calculate(model,case,prepared);result['original_requirement_ids']=case['original_requirement_ids']
    pressure=ledger(case,result)
    item=next(x for x in result['table_results'] if x['product_guid']==guid)
    assert item['coefficient'] is not None
    keys=lambda row:tuple(row[k] for k in ('product_guid','inlet_port_guid','outlet_port_guid'))
    previous={keys(x):x for x in old['table_results']}
    for row in result['table_results']:
        if row['product_guid']==guid:continue
        prior=previous[keys(row)]
        if prior['coefficient'] is None:assert row['coefficient'] is None
        else:assert math.isclose(row['signed_tabulated_contribution_Pa'],prior['signed_tabulated_contribution_Pa'],rel_tol=1e-12,abs_tol=0)
    if name=='maximum':
        prior=next(x for x in old['table_results'] if x['product_guid']==guid)
        assert math.isclose(item['signed_tabulated_contribution_Pa'],prior['signed_tabulated_contribution_Pa'],rel_tol=1e-12,abs_tol=0)
    sub=OUT/name;sub.mkdir()
    (sub/'fitting-data.json').write_text(json.dumps(result,indent=2));(sub/'pressure-ledger.json').write_text(json.dumps(pressure,indent=2))
    summary[name]=dict(finite_paths=result['calculated_table_paths'],numerical_gaps=pressure['numerically_unresolved_fitting_path_count'],outlets=pressure['outlet_count'])
    new_values[name]=item
    pins[str(folder/'analysis.json')]=sha(folder/'analysis.json')
minimum_case=json.loads((RUN/'minimum-flow/analysis.json').read_text())
port=minimum_case['port_flows'][new_values['minimum']['inlet_port_guid']]
q=D(str(port['flow_m3_s']));rho=D(str(minimum_case['air']['density_kg_m3']));mu=D(str(minimum_case['air']['viscosity_Pa_s']))
velocity=q/(D('.5')*D('.4'));diameter=4*D('.5')*D('.4')/(2*(D('.5')+D('.4')))
native_re=rho*velocity*diameter/mu
assert 80000<float(native_re)<100000
k_re=D('1.38')+(native_re-D(80000))/D(20000)*(D('1.30')-D('1.38'))
base=D('.19')+(D('.8')-D('.75'))/D('.25')*(D('.17')-D('.19'))
coefficient=base*k_re;drop=coefficient*rho/2*velocity**2
assert math.isclose(float(coefficient),new_values['minimum']['coefficient'],rel_tol=1e-12,abs_tol=0)
assert math.isclose(float(drop),new_values['minimum']['signed_tabulated_contribution_Pa'],rel_tol=1e-12,abs_tol=0)
assert summary['maximum']==summary['minimum']==dict(finite_paths=29,numerical_gaps=34,outlets=20)
review=dict(publication='2021 ASHRAE Principles of HVAC Ninth Edition online fitting supplement',printed_page=12,
    source_diagram_and_correction_row_visually_inspected=True,scope='Source-bound Reynolds correction extension, not physical applicability or complete pressure acceptance',
    cases=summary,maximum_result_unchanged=True,other_fitting_results_unchanged=True,
    minimum_reynolds_independently_recomputed=float(native_re),minimum_KRe=float(k_re),minimum_coefficient=float(coefficient),minimum_local_dynamic_loss_Pa=float(drop),
    independent_decimal_point_matches=True,pressure_budget_complete=False,design_accepted=False,
    inputs={**pins,str(Path(__file__)):sha(Path(__file__))},
    artifacts={p.relative_to(OUT).as_posix():sha(p) for p in OUT.rglob('*.json')})
(OUT/'review.json').write_text(json.dumps(review,indent=2))
print(json.dumps({k:v for k,v in review.items() if k not in ('inputs','artifacts')},indent=2))
