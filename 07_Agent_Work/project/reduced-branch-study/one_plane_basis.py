"""Bounded one-plane contraction query; original ambiguous headers preserved."""
import copy
import hashlib
import json
import math
from decimal import Decimal as D
from pathlib import Path
import ifcopenshell
from ifcopenshell.util.system import get_ports
from bsa.duct_fitting_data import prepare, calculate
from bsa.source_pressure_ledger import calculate as ledger
from bsa.duct_fitting_chain import shape_hash

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'runs/reduced-branch-network-reviewed'
PARENT=RUN/'reynolds-source-extension'
OUT=RUN/'one-plane-source-extension-reviewed'
if OUT.exists(): raise ValueError('Fresh output required')
OUT.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
basis=json.loads((PARENT/'basis.json').read_text())
model=ifcopenshell.open(str(RUN/'Supply Network.ifc'))
guid='3EOykJlO1HYxMOUeXGrm9C'
obj=model.by_guid(guid)
ports=get_ports(obj)
pin=next(p for p in ports if p.FlowDirection=='SINK')
pout=next(p for p in ports if p.FlowDirection=='SOURCE')
# Visually inspected printed19 Fitting4-2: both literal30-degree columns
# agree at BOTH selected contraction rows. No claim that either label means20.
literal_duplicate_cells=[[0.,0.],[.20,.20]]
assert all(a==b for a,b in literal_duplicate_cells)
table=copy.deepcopy(next(t for t in basis['tables'] if 'transition_family' in t))
table.update(product_guid=guid,geometry_sha256=shape_hash(obj),
    inlet_port_guid=pin.GlobalId,outlet_port_guid=pout.GlobalId,reference_port_guid=pin.GlobalId,
    citation_location='Printed page19,Fitting4-2; selected contraction rows A0/A1=1,2; literal repeated30 and45 degree columns; footnote a',
    transition_family='centred_one_plane',
    applicability_note='Conditional tentative contraction data adapted from round Fitting4-1. Both literal30 columns agree at every selected contraction row; only this common30 ordinate and unambiguous45 ordinate used. No header repair, expansion query or angle snapping. Inlet A0/V0 reference. Physical applicability, developed flow, interaction, station/friction inclusion and complete fan pressure remain unverified.',
    axes=[dict(quantity='inlet_to_outlet_area_ratio',values=[1.,2.]),dict(quantity='major_taper_angle_deg',values=[30.,45.])],
    coefficients=[[0.,0.],[.20,.24]])
basis['tables'].append(table)
path=OUT/'basis.json';path.write_text(json.dumps(basis,indent=2))
prepared,pins=prepare(path)
review={}
for name,folder in [('maximum',RUN),('minimum',RUN/'minimum-flow')]:
    case=json.loads((folder/'analysis.json').read_text())
    old=json.loads((PARENT/name/'fitting-data.json').read_text())
    result=calculate(model,case,prepared)
    result['original_requirement_ids']=case['original_requirement_ids']
    pressure=ledger(case,result)
    key=lambda x:tuple(x[k] for k in ('product_guid','inlet_port_guid','outlet_port_guid'))
    previous={key(x):x for x in old['table_results']}
    for row in result['table_results']:
        if row['product_guid']==guid:continue
        prior=previous[key(row)]
        assert row['coefficient']==prior['coefficient']
        assert row['signed_tabulated_contribution_Pa']==prior['signed_tabulated_contribution_Pa']
    row=next(x for x in result['table_results'] if x['product_guid']==guid)
    native=next(x for x in case['products'] if x['guid']==guid)['transition_geometry']
    assert native['inlet_section_m']==[.5,.45] and native['outlet_section_m']==[.5,.35]
    angle=D(str(native['quantities']['major_taper_angle_deg']))
    coefficient=(D('.45')/D('.35')-1)*(D('.20')+(angle-30)/15*D('.04'))
    velocity=D(str(case['port_flows'][pin.GlobalId]['flow_m3_s']))/(D('.5')*D('.45'))
    drop=coefficient*D(str(case['air']['density_kg_m3']))/2*velocity**2
    assert math.isclose(float(coefficient),row['coefficient'],rel_tol=1e-12)
    assert math.isclose(float(drop),row['signed_tabulated_contribution_Pa'],rel_tol=1e-12)
    assert result['calculated_table_paths']==30
    assert pressure['numerically_unresolved_fitting_path_count']==33
    sub=OUT/name;sub.mkdir()
    (sub/'fitting-data.json').write_text(json.dumps(result,indent=2))
    (sub/'pressure-ledger.json').write_text(json.dumps(pressure,indent=2))
    review[name]=dict(coefficient=row['coefficient'],local_dynamic_loss_Pa=float(drop),finite_paths=30,numerical_gaps=33,independent_decimal_matches=True,other_results_unchanged=True)
record=dict(cases=review,source_page_visually_inspected=True,duplicate_selected_cells_agree=True,
    original_header_not_repaired=True,geometry_unchanged=True,pressure_budget_complete=False,design_accepted=False,
    inputs={**pins,str(Path(__file__)):sha(Path(__file__)),str(RUN/'Supply Network.ifc'):sha(RUN/'Supply Network.ifc')})
(OUT/'review.json').write_text(json.dumps(record,indent=2))
print(json.dumps(review,indent=2))
