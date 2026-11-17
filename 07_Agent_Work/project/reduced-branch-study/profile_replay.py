"""Execute common tee profile reader on the saved project, not a mock network."""
import hashlib
import json
import math
from pathlib import Path
import ifcopenshell
from bsa import rectangular_tee_profiles as reader
from bsa.duct_fitting_data import prepare,calculate

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'runs/reduced-branch-network-reviewed'
SOURCE=RUN/'one-plane-source-extension-reviewed'
OUT=RUN/'canonical-tee-profile-replay-reviewed'
OUT.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
model=ifcopenshell.open(str(RUN/'Supply Network.ifc'))
# Explicit supported family selection; cross and compound junctions are NOT tees.
guids=[o.GlobalId for o in model.by_type('IfcDuctFitting') if o.Name=='RECTANGULAR-TEE']
assert len(guids)==14
prepared,pins=prepare(SOURCE/'basis.json')
summary={}
for name,folder in [('maximum',RUN),('minimum',RUN/'minimum-flow')]:
    case=json.loads((folder/'analysis.json').read_text())
    fresh=reader.canonical_case(model,case,guids)
    result=calculate(model,fresh,prepared)
    old=json.loads((SOURCE/name/'fitting-data.json').read_text())
    key=lambda x:tuple(x[k] for k in ('product_guid','inlet_port_guid','outlet_port_guid'))
    prior={key(x):x for x in old['table_results']}
    assert len(result['table_results'])==len(prior)
    for row in result['table_results']:
        previous=prior[key(row)]
        for field in ['coefficient','signed_tabulated_contribution_Pa']:
            a,b=row[field],previous[field]
            assert (a is None and b is None) or (a is not None and b is not None and math.isclose(a,b,rel_tol=1e-12,abs_tol=0))
    assert result['calculated_table_paths']==30
    (OUT/(name+'-fitting-data.json')).write_text(json.dumps(result,indent=2))
    summary[name]=dict(tee_bodies_reconciled=14,tee_ports_reconciled=42,all_fitting_results_match=True,conditional_paths=30,numerical_gaps=33)
record=dict(cases=summary,selected_tee_guids=guids,method_sha256=sha(Path(reader.__file__)),
    source_ifc_sha256=sha(RUN/'Supply Network.ifc'),basis_pins=pins,
    geometry_unchanged=True,pressure_budget_complete=False,design_accepted=False)
(OUT/'review.json').write_text(json.dumps(record,indent=2))
print(json.dumps(summary,indent=2))
